import numpy as np
import cv2
import mss
import time


class ScreenCapturer:
    def __init__(self, width=800, height=600, fps=60, quality=80):
        self.width = width
        self.height = height
        self.fps = fps
        self.quality = quality
        self.frame_duration = 1.0 / fps
        self.last_frame_time = time.time()

        self.sct = None         # Se inicializa luego
        self.monitor = None

        self.last_keyframe_time = time.time()
        self.last_quality_id = None

    def __iter__(self):
        return self

    def __next__(self):
        # Inicializar mss si aún no fue creado (esto ocurre dentro del hilo)
        if self.sct is None:
            self.sct = mss.mss()
            self.monitor = self.sct.monitors[1]  # Pantalla principal

        now = time.time()
        next_frame_time = self.last_frame_time + self.frame_duration
        sleep_duration = max(0.0, next_frame_time - now)
        if sleep_duration > 0:
            time.sleep(sleep_duration)

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

    def compute_quality_id(self):
        # Ponderaciones, aproximacion
        w_res = 0.00001
        w_fps = 0.5
        w_q = 1.0

        score = w_res * (self.width * self.height) + w_fps * self.fps + w_q * self.quality
        # Valores de referencia
        min_score = 44.8   # aprox 800x600, 30fps, Q=25
        max_score = 150.7  # aprox 1080p, 60fps, Q=100

        # Normalización y escalado
        norm = (score - min_score) / (max_score - min_score)
        norm = max(0.0, min(norm, 1.0))  # Clamp a [0,1]
        quality_id = int(1 + norm * 253)  # Escalado a [1,254]
        return quality_id

    def is_keyframe(self):
        now = time.time()
        quality_id = self.compute_quality_id()

        # Condición 1: ha pasado un intervalo
        #en este caso defini el intervalo en un segundo
        if now - self.last_keyframe_time >= 1.0:
            self.last_keyframe_time = now
            self.last_quality_id = quality_id
            return True, quality_id

        # Condición 2: cambió el quality_id
        if self.last_quality_id is None or quality_id != self.last_quality_id:
            self.last_keyframe_time = now
            self.last_quality_id = quality_id
            return True, quality_id

        return False, quality_id

    def update_config(self, width, height, fps):
        if (width, height, fps) != (self.width, self.height, self.fps):
            print(f"[ENCODER] Resolución cambiada a {width}x{height} @ {fps} FPS")
            self.width = width
            self.height = height
            self.fps = fps
            # Aplica los cambios reales si se necesita reiniciar algún capturador

    #agrego un release, liberando los recursos ocupados de video
    def release(self):
        if self.sct is not None:
            self.sct.close()
            self.sct = None
