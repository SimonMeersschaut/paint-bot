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
    _slots = ("top_left", "top_right", "bottom_left", "bottom_right")
    _feeds = {slot: FeedType.camera_feed for slot in _slots}
    _images = {slot: None for slot in _slots}
    _image_versions = {slot: 0 for slot in _slots}

    @classmethod
    def _grid(cls):
        return [
            {
                "slot": slot,
                "feed": cls._feeds[slot],
                "has_image": cls._images[slot] is not None,
                "version": cls._image_versions[slot],
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
    def init(cls):
        if cls.app is not None:
            return

        cls.app = Flask(__name__, template_folder=str(Path(__file__).parent))
        cls.app.config["TEMPLATES_AUTO_RELOAD"] = True

        @cls.app.route("/", methods=["GET"])
        def home():
            return render_template("home.html", cells=cls._grid(), feed_types=list(FeedType))

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

        @cls.app.route("/feed-image/<slot>", methods=["GET"])
        def feed_image_route(slot):
            if slot not in cls._images:
                abort(404)
            response = cls._image_response(cls._images[slot])
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
    def set_feed_image(cls, slot: str, image):
        if slot not in cls._images:
            raise KeyError(slot)
        cls._images[slot] = image
        cls._image_versions[slot] += 1