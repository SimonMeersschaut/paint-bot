from datetime import datetime
from pathlib import Path
import shutil
import subprocess
from typing import Optional

OUTPUT_DIR = Path("timelapse")
cam = None

try:
    from picamera2 import Picamera2
    cam = None
except ModuleNotFoundError:
    print("Warning: camera not found, continue without?")
    cam = False


def start():
    global cam

    if cam == False:
        return
    cam = Picamera2()
    config = cam.create_still_configuration()
    cam.configure(config)
    cam.start()

def take_picture():
    if cam == False:
        return
    
    if cam is None:
        raise RuntimeError("Camera has not been started.")

    # Output file
    # OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT_DIR / f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    cam.capture_file(str(filename))
    print(f"Saved: {filename}")

def close():
    global cam

    if cam == False:
        return

    if cam is not None:
        cam.close()
        cam = None

def create_timelapse(fps: int = 30):
    if cam == False:
        return
    
    image_paths = sorted(OUTPUT_DIR.glob("photo_*.jpg"))

    if not image_paths:
        raise FileNotFoundError(f"No images found in {OUTPUT_DIR}")

    output_file = OUTPUT_DIR / f"timelapse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to create a timelapse video")

    command = [
        ffmpeg,
        "-y",
        "-framerate",
        str(fps),
        "-pattern_type",
        "glob",
        "-i",
        str(output_dir / "photo_*.jpg"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_file),
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed to create timelapse:\n{result.stderr.strip()}"
        )

    print(f"Saved timelapse: {output_file} ({len(image_paths)} frames)")