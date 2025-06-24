# decoder/bufferlogger.py
import logging
import threading
import time
import queue
from typing import Optional

class BufferLogger:
    def __init__(self, log_file: str = "buffer.log", flush_interval: float = 2.0):
        self.log_file = log_file
        self.flush_interval = flush_interval
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()

        self.logger = logging.getLogger("BufferLogger")
        self.logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(self.log_file)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        fh.setFormatter(formatter)

        self.logger.addHandler(fh)

        self.thread = threading.Thread(target=self._writer_loop, daemon=True)
        self.thread.start()

    def _writer_loop(self):
        while not self.stop_event.is_set():
            try:
                while not self.log_queue.empty():
                    msg = self.log_queue.get_nowait()
                    self.logger.debug(msg)
            except Exception as e:
                print(f"[BufferLogger] Error writing log: {e}")
            time.sleep(self.flush_interval)

    def stop(self):
        self.stop_event.set()
        self.thread.join()
        self._flush_remaining()

    def _flush_remaining(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.logger.debug(msg)

    def log_debug(self, message: str):
        self.log_queue.put(f"DEBUG: {message}")

    def log_buffer_add(self, frame_id: int, buffer_ms: float):
        self.log_queue.put(f"ADD: Frame {frame_id} added. Buffer: {buffer_ms:.2f}ms")

    def log_buffer_drop(self, frame_id: int):
        self.log_queue.put(f"DROP: Frame {frame_id} discarded due to overflow.")

    def log_buffer_state(self, state: str, buffer_ms: float, time_to_wait: Optional[float] = None):
        if time_to_wait:
            self.log_queue.put(f"STATE: {state}. Buffer: {buffer_ms:.2f}ms. Wait: {time_to_wait:.3f}s")
        else:
            self.log_queue.put(f"STATE: {state}. Buffer: {buffer_ms:.2f}ms")

    def log_resync_event(self, frame_id: int, buffer_ms: float):
        self.log_queue.put(f"RESYNC: Keyframe {frame_id} triggered resync. Buffer: {buffer_ms:.2f}ms")
