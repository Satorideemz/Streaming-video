import time
import numpy as np
import struct

class FrameReassembler:
    def __init__(self, payload_size=1400, max_age_s=0.05, chunk_threshold=0.2,
                 width=800, height=600, logger=None): 
        self.frames = {}  # frame_id: { 'chunks': {i: data}, 'timestamp': float, ... }
        self.payload_size = payload_size
        self.max_age_s = max_age_s
        self.chunk_threshold = chunk_threshold
        self.expected_frame_id = 0
        self.logger = logger

        self.last_complete_chunks = {}
        self.last_total_chunks = 0

    def _now(self):
        return time.time()

    def add_chunk(self, packet: bytes):
        if len(packet) < 16:
            return  # Paquete inválido

        frame_id = int.from_bytes(packet[0:2], 'big')
        chunk_index = int.from_bytes(packet[2:4], 'big')
        total_chunks = int.from_bytes(packet[4:6], 'big')
        quality_id = packet[6]
        flags = packet[7]
        timestamp = struct.unpack('>d', packet[8:16])[0]
        payload = packet[16:]

        latency = self._now() - timestamp

        if self.logger:
            self.logger.log_chunk_received()

        if frame_id not in self.frames:
            self.frames[frame_id] = {
                'chunks': {},
                'latencies': [],
                'timestamp': timestamp,
                'total': total_chunks,
                'quality_id': quality_id,
                'flags': flags,
            }

        self.frames[frame_id]['chunks'][chunk_index] = payload
        self.frames[frame_id]['latencies'].append(latency)

    def get_next_frame(self):
        while self.expected_frame_id in self.frames:
            info = self.frames[self.expected_frame_id]
            age = self._now() - info['timestamp']
            received = len(info['chunks'])
            total = info['total']
            latencias = info['latencies']

            # 1. Frame completo
            if received == total:
                chunks = info['chunks']
                frame_data = b''.join(chunks[i] for i in range(total))
                
                # Guardar como último frame válido
                self.last_complete_chunks = chunks.copy()
                self.last_total_chunks = total

                frame_dict = {
                    'frame_id': self.expected_frame_id,
                    'timestamp': info['timestamp'],
                    'frame_data': frame_data,
                    'is_keyframe': bool(info['flags'] & 0b00000001),
                    'quality_id': info['quality_id']
                }

                if self.logger:
                    avg_latency = sum(latencias) / len(latencias) if latencias else 0.0
                    self.logger.log_frame_complete(received, avg_latency)

                del self.frames[self.expected_frame_id]
                self.expected_frame_id = (self.expected_frame_id + 1) % 65536
                return frame_dict

            # 2. Frame parcial aceptable
            elif age > self.max_age_s and (received / total) >= self.chunk_threshold:
                reconstructed_chunks = []
                for i in range(total):
                    if i in info['chunks']:
                        reconstructed_chunks.append(info['chunks'][i])
                    elif i in self.last_complete_chunks:
                        reconstructed_chunks.append(self.last_complete_chunks[i])
                    else:
                        reconstructed_chunks.append(b'\x00' * self.payload_size)

                frame_data = b''.join(reconstructed_chunks)

                frame_dict = {
                    'frame_id': self.expected_frame_id,
                    'timestamp': info['timestamp'],
                    'frame_data': frame_data,
                    'is_keyframe': bool(info['flags'] & 0b00000001),
                    'quality_id': info['quality_id']
                }

                if self.logger:
                    self.logger.log_frame_partial(received)

                del self.frames[self.expected_frame_id]
                self.expected_frame_id = (self.expected_frame_id + 1) % 65536
                return frame_dict

            # 3. Frame descartado por incompleto
            elif age > self.max_age_s:
                if self.logger:
                    self.logger.log_frame_expired(received)

                del self.frames[self.expected_frame_id]
                self.expected_frame_id = (self.expected_frame_id + 1) % 65536
                continue

            break  # Todavía no ha vencido el tiempo de espera

        return None

    def update_config(self, width, height):
        if (width, height) != (self.width, self.height):
            print(f"[REASSEMBLER] Resolución cambiada a {width}x{height}")
            self.width = width
            self.height = height
            # Reconfigura buffers internos si es necesario


