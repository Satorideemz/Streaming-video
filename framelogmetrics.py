import time
import threading
import logging

class FrameLogMetrics:
    def __init__(self, interval_seconds=1, log_path='frame_metrics.log'):
        self.interval = interval_seconds
        self.log_path = log_path

        # Contadores
        self.total_chunks = 0
        self.frame_complete = 0
        self.frame_partial = 0
        self.frame_expired = 0
        self.total_chunks_per_frame = 0
        self.total_frames = 0
        self.total_latency_per_frame = 0.0


        # Inicialización de logging
        logging.basicConfig(
            filename=self.log_path,
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Temporizador
        self.lock = threading.Lock()
        self.last_report_time = time.time()

    def _check_and_report(self):
        now = time.time()
        with self.lock:
            if now - self.last_report_time >= self.interval:
                self._report_locked()
                self._reset_counters_locked()
                self.last_report_time = now

    def _reset_counters_locked(self):
        self.total_chunks = 0
        self.frame_complete = 0
        self.frame_partial = 0
        self.frame_expired = 0
        self.total_chunks_per_frame = 0
        self.total_frames = 0

    def _report_locked(self):
        # Ya estamos dentro del lock
        try:
            avg_chunks = (self.total_chunks_per_frame / self.total_frames) if self.total_frames > 0 else 0
            avg_latency = (self.total_latency_per_frame / self.total_frames) if self.total_frames > 0 else 0.0

            log_msg = (
                f"Frames: {self.total_frames} | "
                f"Completos: {self.frame_complete} | "
                f"Parciales: {self.frame_partial} | "
                f"Vencidos: {self.frame_expired} | "
                f"Chunks totales: {self.total_chunks} | "
                f"Chunks por frame (prom.): {avg_chunks:.2f} | "
                f"Latencia promedio (s): {avg_latency:.4f}"
            )

            logging.info(log_msg)
        except Exception as e:
            logging.error(f"[ERROR] Al registrar métricas: {e}")

    # Métodos públicos de log
    def log_chunk_received(self):
        with self.lock:
            self.total_chunks += 1
        self._check_and_report()

    def log_frame_complete(self, received_chunks, avg_latency):
        with self.lock:
            self.frame_complete += 1
            self.total_frames += 1
            self.total_chunks_per_frame += received_chunks
            self.total_latency_per_frame += avg_latency
        self._check_and_report()

    def log_frame_partial(self, received_chunks):
        with self.lock:
            self.frame_partial += 1
            self.total_frames += 1
            self.total_chunks_per_frame += received_chunks
        self._check_and_report()

    def log_frame_expired(self, received_chunks):
        with self.lock:
            self.frame_expired += 1
            self.total_frames += 1
            self.total_chunks_per_frame += received_chunks
        self._check_and_report()
