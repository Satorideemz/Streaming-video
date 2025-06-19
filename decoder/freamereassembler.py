import time
import numpy as np
import struct

class FrameReassembler:
    #Edad maxima corresponde al maximo tiempo de retraso en que un frame es aceptado
    #Chunk threshold es el minimo de chunks recibidos para iniciar una reconstruccion 
    def __init__(self, payload_size=1400, max_age_s=0.05, chunk_threshold=0.2,
                 width=800, height=600,logger=None): 
        self.frames = {}  # frame_id: { 'chunks': {i: data}, 'timestamp': float, 'total': int }
        self.payload_size = payload_size
        self.max_age_s = max_age_s
        self.chunk_threshold = chunk_threshold
        self.width = width
        self.height = height
        self.expected_frame_id = 0
        self.last_complete_chunks = {}
        self.green_frame = self._create_green_frame().tobytes()
        self.logger = logger

    def _create_green_frame(self):
        return np.full((self.height, self.width, 3), (0, 255, 0), dtype=np.uint8)

    def _now_ms(self):
        return time.time()

    def add_chunk(self, packet: bytes):
        if len(packet) < 16:
            return  # Paquete inválido

        # Parsear nueva cabecera
        frame_id = int.from_bytes(packet[0:2], 'big')
        chunk_index = int.from_bytes(packet[2:4], 'big')
        total_chunks = int.from_bytes(packet[4:6], 'big')
        quality_id = packet[6]
        flags = packet[7]
        timestamp = struct.unpack('>d', packet[8:16])[0]
        payload = packet[16:]

        latency = time.time() - timestamp

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
            age = self._now_ms() - info['timestamp']
            received = len(info['chunks'])
            total = info['total']
            latencias = info['latencies']

            # 1. Si frame completo
            if received == total:
                chunks = info['chunks']
                reconstructed = self._reconstruct_from_chunks(chunks, total)
                self.last_complete_chunks = chunks.copy()
                del self.frames[self.expected_frame_id]
                self.expected_frame_id = (self.expected_frame_id + 1) % 65536

                if self.logger:
    
                    avg_latency = sum(latencias) / len(latencias) if latencias else 0.0                    
                    self.logger.log_frame_complete(received,avg_latency)
                return reconstructed

            # 2. Si frame vencido y al menos chunk_threshold
            if age > self.max_age_s:
                if received / total >= self.chunk_threshold:
                    chunks = info['chunks']
                    reconstructed = self._reconstruct_from_chunks(chunks, total)
                    self.last_complete_chunks = chunks.copy()
                    del self.frames[self.expected_frame_id]
                    self.expected_frame_id = (self.expected_frame_id + 1) % 65536

                    if self.logger:
                        self.logger.log_frame_partial(received)
                    return reconstructed
                else:
                    # Descartar frame por insuficiencia
                    del self.frames[self.expected_frame_id]
                    self.expected_frame_id = (self.expected_frame_id + 1) % 65536

                    if self.logger:
                        self.logger.log_frame_expired(received)
                    if self.last_complete_chunks:
                        return self._reconstruct_from_chunks(self.last_complete_chunks, total)
                    else:
                        return self.green_frame

            # 3. Aún no se cumplen condiciones
            break

        return None


    def _reconstruct_from_chunks(self, chunks: dict, total: int) -> bytes:
        frame = bytearray()
        for i in range(total):
            if i in chunks:
                frame.extend(chunks[i])
            elif i in self.last_complete_chunks:
                frame.extend(self.last_complete_chunks[i])
            else:
                frame.extend(b'\x00' * self.payload_size)  # Relleno con ceros
        return bytes(frame)

    def update_config(self, width, height):
        if (width, height) != (self.width, self.height):
            print(f"[REASSEMBLER] Resolución cambiada a {width}x{height}")
            self.width = width
            self.height = height
            # Reconfigura buffers internos si es necesario


