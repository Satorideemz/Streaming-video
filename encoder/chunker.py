import struct
import time
import math

class Chunker:
    def __init__(self, payload_size=1400):
        self.payload_size = payload_size
        self.frame_id = 0

    def chunk_frame(self, frame_data: bytes):
        chunks = []
        total_chunks = math.ceil(len(frame_data) / self.payload_size)
        timestamp = time.time()  # segundos con decimales

        for i in range(total_chunks):
            start = i * self.payload_size
            end = start + self.payload_size
            payload = frame_data[start:end]

            # Cabecera: 2 bytes frame_id + 2 bytes chunk_index + 2 bytes total_chunks + 8 bytes timestamp
            header = (
                self.frame_id.to_bytes(2, 'big') +
                i.to_bytes(2, 'big') +
                total_chunks.to_bytes(2, 'big') +
                struct.pack('>d', timestamp)
            )
            chunks.append(header + payload)

        self.frame_id = (self.frame_id + 1) % 65536
        return chunks
