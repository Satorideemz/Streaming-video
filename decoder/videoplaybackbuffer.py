# decoder/videoplaybackbuffer.py
import time
import collections
import threading
from typing import Optional, Tuple, Dict, Any

class VideoPlaybackBuffer:
    def __init__(self, initial_buffer_ms: int = 5, max_buffer_ms: int =50,
                 min_buffer_ms: int = 50, fps: int = 60, logger: Any = None):
        self.buffer = collections.deque()
        self.lock = threading.Lock()
        self.logger = logger

        self.initial_buffer_size_ms = initial_buffer_ms
        self.max_buffer_size_ms = max_buffer_ms
        self.min_buffer_size_ms = min_buffer_ms
        self.expected_frame_duration_ms = (1000.0 / fps) if fps > 0 else 33.33

        self.last_playback_time_client = None
        self.last_playback_timestamp_server = None
        self.is_playing = False
        self.last_keyframe_info = None

        if self.logger:
            self.logger.log_debug("[JITTER_BUFFER] Inicializando buffer.")

    def _get_current_buffer_duration_ms(self) -> float:
        if not self.buffer:
            return 0.0
        if len(self.buffer) == 1:
            return self.expected_frame_duration_ms
        return (self.buffer[-1]['timestamp'] - self.buffer[0]['timestamp']) * 1000.0

    def _clean_buffer_on_overflow(self):
        while self._get_current_buffer_duration_ms() > self.max_buffer_size_ms and len(self.buffer) > 1:
            dropped_frame_info = self.buffer.popleft()
            if self.logger:
                self.logger.log_buffer_drop(dropped_frame_info['frame_id'])
                self.logger.log_debug(f"[JITTER_BUFFER] Descartado frame {dropped_frame_info['frame_id']} por overflow. Buffer: {self._get_current_buffer_duration_ms():.2f}ms")

    def add_frame(self, frame: Dict[str, Any]):
        with self.lock:
            frame_id = frame["frame_id"]
            if self.buffer and frame_id <= self.buffer[-1]["frame_id"] and not frame["is_keyframe"]:
                if self.logger:
                    self.logger.log_debug(f"[JITTER_BUFFER] Descartado frame {frame_id} (demasiado antiguo/duplicado).")
                return

            self.buffer.append(frame)
            self._clean_buffer_on_overflow()

            if self.logger:
                current_duration = self._get_current_buffer_duration_ms()
                self.logger.log_buffer_add(frame_id, current_duration)
                self.logger.log_debug(f"[JITTER_BUFFER] Añadido frame {frame_id}. Buffer: {current_duration:.2f}ms")

    def get_frame_for_display(self) -> Optional[Tuple[bytes, Dict[str, Any]]]:
        with self.lock:
            if not self.buffer:
                self.is_playing = False
                if self.logger:
                    self.logger.log_buffer_state("Underflow (empty)", 0.0)
                return None, None

            current_time_client = time.time()
            next_frame_info = self.buffer[0]

            if not self.is_playing:
                if self._get_current_buffer_duration_ms() < self.initial_buffer_size_ms:
                    if self.logger:
                        self.logger.log_buffer_state("Buffering (initial fill)", self._get_current_buffer_duration_ms())
                    return None, None

                self.last_playback_time_client = current_time_client
                self.last_playback_timestamp_server = next_frame_info['timestamp']
                self.is_playing = True
                if self.logger:
                    self.logger.log_buffer_state("Playback started", self._get_current_buffer_duration_ms())

            if next_frame_info['is_keyframe']:
                if self.last_keyframe_info is None or \
                   abs((next_frame_info['timestamp'] - self.last_keyframe_info['timestamp_server']) - \
                       (current_time_client - self.last_keyframe_info['time_client'])) > (self.expected_frame_duration_ms / 1000.0 * 2):
                    if self.logger:
                        self.logger.log_debug(f"[JITTER_BUFFER] Keyframe {next_frame_info['frame_id']} detectado. Resincronizando.")
                        self.logger.log_resync_event(next_frame_info['frame_id'], self._get_current_buffer_duration_ms())
                    self.last_playback_time_client = current_time_client
                    self.last_playback_timestamp_server = next_frame_info['timestamp']
                    self.last_keyframe_info = {
                        'timestamp_server': next_frame_info['timestamp'],
                        'time_client': current_time_client
                    }

            expected_playback_time_client = self.last_playback_time_client + \
                                            (next_frame_info['timestamp'] - self.last_playback_timestamp_server)

            if current_time_client >= expected_playback_time_client:
                frame_to_display = self.buffer.popleft()
                self.last_playback_time_client = current_time_client
                self.last_playback_timestamp_server = frame_to_display['timestamp']

                if self.logger:
                    self.logger.log_buffer_state("Frame delivered", self._get_current_buffer_duration_ms())

                metadata = {
                    k: v for k, v in frame_to_display.items()
                    if k != "frame_data"
                }

                return frame_to_display["frame_data"], metadata
            else:
                if self.logger:
                    self.logger.log_buffer_state("Waiting for playback time", self._get_current_buffer_duration_ms(),
                                                 time_to_wait=(expected_playback_time_client - current_time_client))
                return None, None

    def push_and_get(self, frame: Optional[Dict[str, Any]]) -> Optional[Tuple[bytes, Dict[str, Any]]]:
        """
        Método externo para integrar con el main: intenta añadir y obtener un frame para mostrar.
        """
        if frame is not None:
            self.add_frame(frame)
        return self.get_frame_for_display()

    def is_ready(self) -> bool:
        with self.lock:
            return self._get_current_buffer_duration_ms() >= self.initial_buffer_size_ms

    def get_buffer_duration_ms(self) -> float:
        with self.lock:
            return self._get_current_buffer_duration_ms()

    def clear(self):
        with self.lock:
            self.buffer.clear()
            self.last_playback_time_client = None
            self.last_playback_timestamp_server = None
            self.is_playing = False
            self.last_keyframe_info = None
            if self.logger:
                self.logger.log_buffer_state("Buffer cleared", 0.0)
            print("[JITTER_BUFFER] Buffer limpiado y estado reseteado.")
