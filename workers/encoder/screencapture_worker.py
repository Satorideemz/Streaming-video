import threading
import collections
from typing import Optional
from encoder.screencapturer import ScreenCapturer
import time

class ScreenCaptureWorker:
    """
    Clase encargada de capturar frames de pantalla en un hilo separado,
    utilizando una instancia de ScreenCapturer.
    """
    def __init__(self, capturer: ScreenCapturer, buffer_size: int = 1):
        self.capturer = capturer
        self.buffer = collections.deque(maxlen=buffer_size)
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.running = False

    def start(self):
        """Inicia el hilo de captura."""
        self.running = True
        self.thread.start()

    def stop(self):
        """Detiene el hilo de captura y libera recursos."""
        self.running = False
        self.thread.join()
        self.capturer.release()

    def _capture_loop(self):
        """Loop interno del hilo que captura frames JPEG."""
        while self.running:
            try:
                
                frame_bytes = next(self.capturer)
                with self.lock:
                    self.buffer.append(frame_bytes)
            except Exception as e:
                print(f"[WORKER] Error capturando frame: {e}")

    def get_latest_frame(self, sync_with_fps: bool = True) -> Optional[bytes]:
        if sync_with_fps:
            time.sleep(self.capturer.frame_duration)

        with self.lock:
            if self.buffer:
                return self.buffer[-1]
            else:
                return None


    def is_keyframe(self) -> tuple[bool, int]:
        """Delegado directo al capturador."""
        return self.capturer.is_keyframe()

    def update_config(self, width: int, height: int, fps: int):
        """Actualiza la configuración del capturador si es necesario."""
        self.capturer.update_config(width, height, fps)
