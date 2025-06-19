import cv2
import numpy as np

class LiveVideoViewer:
    def __init__(self, window_name="Pantalla Remota", width=800, height=600, fps=60):
        self.window_name = window_name
        self.width = width
        self.height = height
        self.fps = fps
        self.delay = int(1000 / fps)  # Milisegundos entre frames

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, width, height)

    def decode_and_display(self, frame_data: bytes):
        # Decodificar desde JPEG
        img_array = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if frame is None:
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        else:
            frame = cv2.resize(frame, (self.width, self.height))

        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(self.delay)
        return key != 27  # True = continuar, False = salir si se presiona ESC

    def update_config(self, width, height, fps):
        if (width, height, fps) != (self.width, self.height, self.fps):
            print(f"[DECODER] Resolución cambiada a {width}x{height} @ {fps} FPS")
            self.width = width
            self.height = height
            self.fps = fps
            # Reconfigura si estás usando temporizador u otros buffers visuales

    def release(self):
        cv2.destroyAllWindows()

