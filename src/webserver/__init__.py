from enum import Enum, auto
from io import BytesIO
from pathlib import Path
from threading import Thread

from flask import Flask, abort, redirect, render_template, request, send_file, url_for


class FeedType(Enum):
    camera_feed = auto()
    target_feed = auto()
    expected_feed = auto()


class WebApp:
    app = None
    _thread = None
    _on_fan_change = None
    _fan_mode = False
    _slots = ("top_left", "top_right", "bottom_left", "bottom_right")
    _feeds = {slot: FeedType.camera_feed for slot in _slots}
    _images = {feed_type: None for feed_type in FeedType}
    _image_versions = {feed_type: 0 for feed_type in FeedType}

    @classmethod
    def _grid(cls):
        return [
            {
                "slot": slot,
                "feed": cls._feeds[slot],
                "has_image": cls._images[cls._feeds[slot]] is not None,
                "version": cls._image_versions[cls._feeds[slot]],
            }
            for slot in cls._slots
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
            import cv2

            ok, encoded = cv2.imencode(".png", image)
            if ok:
                return send_file(BytesIO(encoded.tobytes()), mimetype="image/png", max_age=0)
        except Exception:
            pass

        abort(415)

    @classmethod
    def init(cls, *, on_fan_change=None):
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
            )

        @cls.app.route("/set-feed", methods=["POST"])
        def set_feed_route():
            slot = request.form.get("slot", "")
            feed_name = request.form.get("feed", "")

            try:
                feed = FeedType[feed_name]
                cls.set_feed(slot, feed)
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

    @classmethod
    def _run(cls):
        cls.app.run(threaded=True, use_reloader=False)

    @classmethod
    def start(cls):
        cls.init()
        if cls._thread and cls._thread.is_alive():
            return cls._thread

        cls._thread = Thread(target=cls._run, daemon=True)
        cls._thread.start()
        return cls._thread

    @classmethod
    def set_feed(cls, slot: str, type: FeedType):
        if slot not in cls._feeds:
            raise KeyError(slot)
        cls._feeds[slot] = type

    @classmethod
    def set_feed_image(cls, feed_type: FeedType, image):
        if not isinstance(feed_type, FeedType):
            feed_type = FeedType[feed_type]
        cls._images[feed_type] = image
        cls._image_versions[feed_type] += 1