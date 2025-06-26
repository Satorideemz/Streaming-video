import threading
import queue
import collections
from typing import Optional, Dict, List
from encoder.chunker import Chunker
import struct
import time

class ChunkerWorker:
    """
    Worker que divide frames en chunks utilizando un hilo separado,
    sincronizado con los frames capturados.
    """
    def __init__(self, chunker: Chunker):
        self.chunker = chunker
        self.input_queue = queue.Queue(maxsize=3)  # evita saturar la cola
        self.buffer = collections.deque(maxlen=1)
        self.lock = threading.Lock()
        self.running = False
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        """Inicia el hilo de procesamiento."""
        self.running = True
        self.thread.start()

    def stop(self):
        """Detiene el hilo y desbloquea si está esperando."""
        self.running = False
        self.input_queue.put(None)
        self.thread.join()

    def enqueue_frame(self, frame_data: bytes, quality_id: int, is_keyframe: bool):
        """
        Coloca un nuevo frame en la cola para procesar.
        Si la cola está llena, descarta el más antiguo (opcional).
        """
        try:
            self.input_queue.put_nowait((frame_data, quality_id, is_keyframe))
        except queue.Full:
            # opcional: descartar o reemplazar
            pass  # Silenciosamente ignora si está llena (para evitar backpressure)

    def get_latest_chunks(self,fps=None) -> Optional[Dict]:
        """Devuelve el último lote de chunks generado (si lo hay)."""
        time.sleep (1/(fps*2)) #ajusta la frecuencia de llamado a los fps
        with self.lock:
            return self.buffer[-1] if self.buffer else None

    def _run(self):
        """Bucle principal de procesamiento del hilo."""
        while self.running:
            try:
                item = self.input_queue.get(timeout=0.1)
            except queue.Empty:
                continue  # Espera nueva entrada

            if item is None:
                break  # Señal de cierre

            frame_data, quality_id, is_keyframe = item

            if not frame_data:
                continue  # Seguridad: no procesar vacío

            # Dividir el frame en chunks
            chunks = self.chunker.chunk_frame(frame_data, quality_id, is_keyframe)

            if not chunks:
                continue  # Seguridad adicional

            frame_id = int.from_bytes(chunks[0][0:2], 'big')
            timestamp = struct.unpack('>d', chunks[0][8:16])[0]

            frame_info = {
                "chunks": chunks,
                "frame_id": frame_id,
                "quality_id": quality_id,
                "is_keyframe": is_keyframe,
                "timestamp": timestamp
            }

            with self.lock:
                self.buffer.append(frame_info)
