from encoder.chunker import Chunker
from encoder.screencapturer import ScreenCapturer
from decoder.freamereassembler import FrameReassembler
from decoder.livevideoviewer import LiveVideoViewer
from framelogmetrics import FrameLogMetrics

# Configuración inicial
VIDEO_PATH = 'file-example.mp4'
OUTPUT_PATH = 'output.mp4'
WIDTH, HEIGHT = 800, 600
FPS = 30
PAYLOAD_SIZE = 1400

# Inicialización
encoder = ScreenCapturer( width=WIDTH, height=HEIGHT, fps=FPS)
chunker = Chunker(payload_size=PAYLOAD_SIZE)  # asumimos que ya lo tenés definido

log = FrameLogMetrics()
reassembler = FrameReassembler(payload_size=PAYLOAD_SIZE, width=WIDTH, height=HEIGHT,logger=log)

decoder = LiveVideoViewer( width=WIDTH, height=HEIGHT, fps=FPS)

try:
    for encoded_frame in encoder:
        # Simular envío por red en chunks
        chunks = chunker.chunk_frame(encoded_frame)
        for chunk in chunks:
            reassembler.add_chunk(chunk)

        # Simular recepción por parte del consumidor
        frame_bytes = reassembler.get_next_frame()
        if frame_bytes:
            #decoder.decode_and_write(frame_bytes)
            decoder.decode_and_display(frame_bytes)

finally:
    encoder.release()
    decoder.release()

