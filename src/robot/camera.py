from datetime import datetime
from pathlib import Path
import shutil
import subprocess
from PIL import Image

OUTPUT_DIR = Path("timelapse")
cam = None

try:
    from picamera2 import Picamera2
    cam = None
except ModuleNotFoundError:
    print("Warning: camera not found, continue without?")
    cam = False


class Camera:
    @classmethod
    def start(cls):
        global cam

        if cam == False:
            return
            
        cam = Picamera2()
        config = cam.create_still_configuration()
        cam.configure(config)
        cam.start()

    @classmethod
    def take_picture_and_return(cls, filename=None):
        if cam == False:
            return
        
        if cam is None:
            raise RuntimeError("Camera has not been started.")

        if filename is None:
            filename = OUTPUT_DIR / f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        # 1. Capture the image as a NumPy array directly from the camera
        img_array = cam.capture_array()

        # 2. Convert the array to a PIL Image
        img = Image.fromarray(img_array)

        # 3. Apply the software flips
        # FLIP_LEFT_RIGHT handles the horizontal flip
        # FLIP_TOP_BOTTOM handles the vertical flip
        flipped_img = img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)

        # 4. Save the transformed image to your file path
        flipped_img.save(str(filename))
        
        print(f"Saved: {filename}")

        return flipped_img

    @classmethod
    def close(cls):
        global cam

        if cam == False:
            return

        if cam is not None:
            cam.close()
            cam = None

    @classmethod
    def create_timelapse(cls, fps: int = 10):
        
        output_file = OUTPUT_DIR / f"timelapse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("ffmpeg is required to create a timelapse video")

        # 1. Gather and sort all the frames
        photo_files = sorted(OUTPUT_DIR.glob("photo_*.jpg"))
        if not photo_files:
            print("No photos found to create a timelapse.")
            return

        print(f"Processing {len(photo_files)} frames into a timelapse...")

        # 2. Build the command using image2pipe
        command = [
            ffmpeg,
            "-y",
            "-f", "image2pipe",       # Tell FFmpeg to expect a stream of images
            "-vcodec", "mjpeg",       # The input stream consists of JPEGs
            "-r", str(fps),           # Input frame rate
            "-i", "-",                # Read from stdin (piped from Python)
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),           # Output frame rate
            str(output_file),
        ]

        # 3. Open the FFmpeg subprocess with a pipe for stdin
        process = subprocess.Popen(
            command, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )

        try:
            # 4. Feed every single photo's raw bytes directly to FFmpeg
            for photo in photo_files:
                with open(photo, "rb") as f:
                    process.stdin.write(f.read())
            
            # Close stdin to signal to FFmpeg that the image stream is finished
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise RuntimeError(
                    f"ffmpeg failed to create timelapse:\n{stderr.decode('utf-8').strip()}"
                )

            print(f"Successfully saved timelapse: {output_file}")

        except Exception as e:
            # Ensure the process is terminated if something goes wrong during the loop
            process.kill()
            raise e