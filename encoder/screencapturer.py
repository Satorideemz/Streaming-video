import numpy as np
import cv2
import mss
import time

class ScreenCapturer:
    def __init__(self, width=800, height=600, fps=30, quality=80):
        self.width = width
        self.height = height
        self.fps = fps
        self.quality = quality
        self.frame_duration = 1.0 / fps
        self.last_frame_time = time.time()
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]  # Pantalla principal

    def __iter__(self):
        return self

    def __next__(self):
        now = time.time()
        elapsed = now - self.last_frame_time
        if elapsed < self.frame_duration:
            time.sleep(self.frame_duration - elapsed)
        self.last_frame_time = time.time()

        # Captura en vivo
        screenshot = self.sct.grab(self.monitor)
        frame = np.array(screenshot)[:, :, :3]  # BGR

        # Redimensionar y comprimir
        frame = cv2.resize(frame, (self.width, self.height))
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
        success, encoded = cv2.imencode('.jpg', frame, encode_param)
        if not success:
            raise RuntimeError("Error al codificar el frame de pantalla")
        return encoded.tobytes()
