import cv2
import numpy as np

class LiveVideoViewer:
    def __init__(self, window_name="Pantalla Remota", width=800, height=600):
        self.window_name = window_name
        self.width = width
        self.height = height
        self.fullscreen = False  # Estado inicial

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, width, height)

    def decode_and_display(self, frame_data: bytes):
        img_array = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if frame is None:
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        else:
            frame = cv2.resize(frame, (self.width, self.height))

        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(1) & 0xFF

        # Manejo de la tecla "k"
        if key == ord('k'):
            self.toggle_fullscreen()

        # Salir con ESC
        return key != 27

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, self.width, self.height)

    def update_config(self, width, height, fps):
        if (width, height, fps) != (self.width, self.height, self.fps):
            print(f"[DECODER] Resolución cambiada a {width}x{height} @ {fps} FPS")
            self.width = width
            self.height = height
            self.fps = fps

    def release(self):
        cv2.destroyAllWindows()
