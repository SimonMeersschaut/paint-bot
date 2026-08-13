from enum import Enum, auto
from io import BytesIO
from pathlib import Path
from threading import Thread
import glob
import cv2
from robot import Camera

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, url_for


class FeedType(Enum):
    camera_feed = auto()
    target_feed = auto()
    expected_feed = auto()


class WebApp:
    app = None
    _on_fan_change = None
    _fan_mode = True # starts `on`
    _printer = None
    _running = False

    _progress = 0.0
    _slots = 2
    _feeds = [FeedType.camera_feed, FeedType.expected_feed]
    _images = {feed_type: None for feed_type in FeedType}
    _image_versions = {feed_type: 0 for feed_type in FeedType}
    _project = ""

    @classmethod
    def get_projects(cls) -> list[str]:
        files = glob.glob("data/stroke_renders/*.json")
        project_names = [Path(file).stem for file in files]
        return project_names

    @classmethod
    def set_project(cls, project: str):
        if not project in cls.get_projects():
            raise ValueError("Project not valid.")
            
        cls._project = project

    @classmethod
    def _grid(cls):
        return [
            {
                "slot": slot_idx,
                "feed": cls._feeds[slot_idx],
                "has_image": cls._images[cls._feeds[slot_idx]] is not None,
                "version": cls._image_versions[cls._feeds[slot_idx]],
            }
            for slot_idx in range(cls._slots)
        ]

    @classmethod
    def _image_response(cls, image):
        if image is None:
            abort(404)

        if isinstance(image, (bytes, bytearray, memoryview)):
            return send_file(BytesIO(image), mimetype="image/jpeg", max_age=0)

        if hasattr(image, "save"):
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            return send_file(buffer, mimetype="image/png", max_age=0)

        try:
            ok, encoded = cv2.imencode(".png", image)
            if ok:
                return send_file(BytesIO(encoded.tobytes()), mimetype="image/png", max_age=0)
        except Exception:
            pass

        abort(415)

    @classmethod
    def init(cls, printer, *, on_fan_change=None):
        cls._printer = printer
        if on_fan_change is not None and not callable(on_fan_change):
            raise TypeError("on_fan_change must be callable or None")

        if on_fan_change is not None:
            cls._on_fan_change = on_fan_change

        if cls.app is not None:
            return

        cls.app = Flask(__name__, template_folder=str(Path(__file__).parent))
        cls.app.config["TEMPLATES_AUTO_RELOAD"] = True

        @cls.app.route("/", methods=["GET"])
        def home():
            return render_template(
                "home.html",
                cells=cls._grid(),
                feed_types=list(FeedType),
                fan_mode=cls._fan_mode,
                running=cls._running,
                progress=cls._progress,
                projects=cls.get_projects(),
                current_project=cls._project,
            )

        @cls.app.route("/set-feed", methods=["POST"])
        def set_feed_route():
            slot_idx = int(request.form.get("slot", 0))
            feed_name = request.form.get("feed", "")

            try:
                feed = FeedType[feed_name]
                cls.set_feed(slot_idx, feed)
            except (KeyError, AttributeError):
                pass

            return redirect(url_for("home"))

        @cls.app.route("/set-fan", methods=["POST"])
        def set_fan_route():
            mode_value = request.form.get("mode", "").strip().lower()

            if mode_value in {"on", "1", "true", "yes"}:
                mode = True
            elif mode_value in {"off", "0", "false", "no"}:
                mode = False
            else:
                mode = not cls._fan_mode

            if cls._on_fan_change is not None:
                cls._on_fan_change(mode)

            cls._fan_mode = mode

            return redirect(url_for("home"))

        @cls.app.route("/set-project", methods=["POST"])
        def set_project_route():
            project = request.form.get("project", "").strip()
            if project:
                cls.set_project(project)
            return redirect(url_for("home"))

        @cls.app.route("/feed-image/<feed_name>", methods=["GET"])
        def feed_image_route(feed_name):
            try:
                feed_type = FeedType[feed_name]
            except KeyError:
                abort(404)
            response = cls._image_response(cls._images[feed_type])
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            return response

        @cls.app.route("/progress", methods=["GET"])
        def progress_route():
            return jsonify(progress=cls._progress)

        @cls.app.route("/start", methods=["POST"])
        def start_route():
            from execution import ExecutionDaemon
            kwargs = {"printer": cls._printer, "project_name": cls._project}
            cls._execution_thread = Thread(target=ExecutionDaemon.run_thread, kwargs=kwargs, daemon=True)
            cls._execution_thread.start()
            cls._running = True
            return redirect(url_for("home"))

        @cls.app.route("/stop", methods=["POST"])
        def stop_route():
            cls._running = False
            return redirect(url_for("home"))

    @classmethod
    def _run(cls):
        cls.app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)

    @classmethod
    def start_server(cls):
        Camera.start()
        cls._printer.connect()
        cls._run()

    @classmethod
    def set_feed(cls, slot_idx: int, type: FeedType):
        if slot_idx > cls._slots:
            raise KeyError(slot_idx)
        cls._feeds[slot_idx] = type

    @classmethod
    def set_feed_image(cls, feed_type: FeedType, image):
        if not isinstance(feed_type, FeedType):
            feed_type = FeedType[feed_type]
        cls._images[feed_type] = image
        cls._image_versions[feed_type] += 1

    @classmethod
    def set_progress(cls, progress: float):
        progress_value = float(progress)
        cls._progress = max(0.0, min(1.0, progress_value))