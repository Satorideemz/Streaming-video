import threading
import queue
from typing import Optional, Tuple
from decoder.videoplaybackbuffer import VideoPlaybackBuffer
import time

class VideoPlaybackBufferWorker:
    """
    Worker que se encarga de manejar el VideoPlaybackBuffer en un hilo separado.
    Recibe frames desde una cola de entrada, los añade al buffer, y extrae frames
    listos para ser reproducidos, poniéndolos en la cola de salida.
    """
    def __init__(self,
                 video_buffer: VideoPlaybackBuffer,
                 input_queue: queue.Queue,
                 output_queue: Optional[queue.Queue] = None,
                 max_output_size: int = 60):
        
        self.video_buffer = video_buffer
        self.input_queue = input_queue
        self.output_queue = output_queue or queue.Queue(maxsize=max_output_size)

        self.running = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.stop_event = threading.Event()

    def start(self):
        """Inicia el hilo de reproducción."""
        if not self.running:
            self.running = True
            self.thread.start()
            print("[PLAYBACK WORKER] Hilo iniciado.")

    def stop(self):
        """Detiene el hilo de forma segura."""
        self.running = False
        self.stop_event.set()
        self.thread.join()
        print("[PLAYBACK WORKER] Hilo detenido.")

    def get_next_decoded_frame(self, timeout: Optional[float] = None) -> Optional[Tuple[bytes, dict]]:
        """
        Devuelve el próximo frame listo para decodificar.
        :return: Tupla (frame_data, metadata) o None si no hay.
        """
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _run(self):
        """Loop principal del worker de reproducción."""
        print("[PLAYBACK WORKER] Loop de reproducción iniciado.")
        while self.running and not self.stop_event.is_set():
            try:

                # Espera un nuevo frame ensamblado
                frame = self.input_queue.get(timeout=0.1)
                if frame:
                    self.video_buffer.add_frame(frame)

                # Intentar extraer frame para mostrar
                frame_data, metadata = self.video_buffer.get_frame_for_display()

                if frame_data:
                    try:
                        self.output_queue.put((frame_data, metadata), timeout=0.1)
                        print(f"[PLAYBACK WORKER] Frame listo para mostrar (ID: {metadata.get('frame_id', 'N/A')})")
                    except queue.Full:
                        print("[PLAYBACK WORKER] Cola de salida llena, descartando frame.")
            except queue.Empty:
                continue
