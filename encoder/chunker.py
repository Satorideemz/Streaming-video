import time
import math
import struct

class Chunker:
    def __init__(self, payload_size=1400):
        self.payload_size = payload_size
        self.frame_id = 0

    def chunk_frame(self, frame_data: bytes, quality_id: int, is_keyframe: bool):
        chunks = []
        total_chunks = math.ceil(len(frame_data) / self.payload_size)
        timestamp = time.time()

        flags = 0b00000001 if is_keyframe else 0b00000000
        quality_id = max(0, min(quality_id, 255))  # Clamp por seguridad

        for i in range(total_chunks):
            start = i * self.payload_size
            end = start + self.payload_size
            payload = frame_data[start:end]

            header = (
                self.frame_id.to_bytes(2, 'big') +
                i.to_bytes(2, 'big') +
                total_chunks.to_bytes(2, 'big') +
                quality_id.to_bytes(1, 'big') +
                flags.to_bytes(1, 'big') +
                struct.pack('>d', timestamp)
            )
            chunks.append(header + payload)

        self.frame_id = (self.frame_id + 1) % 65536
        return chunks