from encoder.chunker import Chunker
from encoder.screencapturer import ScreenCapturer
from decoder.freamereassembler import FrameReassembler
from decoder.livevideoviewer import LiveVideoViewer
from decoder.videoplaybackbuffer import VideoPlaybackBuffer
from logger.framelogmetrics import FrameLogMetrics
from logger.bufferlogger import BufferLogger

# Configuración
WIDTH, HEIGHT = 800, 600
FPS = 30
PAYLOAD_SIZE = 1400

# Inicialización de módulos
encoder = ScreenCapturer(width=WIDTH, height=HEIGHT, fps=FPS)
chunker = Chunker(payload_size=PAYLOAD_SIZE)
log = FrameLogMetrics()

reassembler = FrameReassembler(payload_size=PAYLOAD_SIZE, width=WIDTH, height=HEIGHT, logger=log)

decoder = LiveVideoViewer(width=WIDTH, height=HEIGHT)

#nuevo: añado logger en buffer
log = FrameLogMetrics()
buffer_logger = BufferLogger(log_file="buffer.log")

playbackbuffer = VideoPlaybackBuffer(fps=FPS, logger=buffer_logger)


try:
    for encoded_frame in encoder:
        # Simular chunks como si vinieran por red
        chunks = chunker.chunk_frame(
            encoded_frame,
            quality_id=encoder.compute_quality_id(),
            is_keyframe=encoder.is_keyframe()
        )
        for chunk in chunks:
            reassembler.add_chunk(chunk)

        # Recuperar y enviar a buffer y decodificador
        frame = reassembler.get_next_frame()
        frame_data, _ = playbackbuffer.push_and_get(frame)

        if frame_data:
            decoder.decode_and_display(frame_data)

finally:
    encoder.release()
    decoder.release()
    buffer_logger.stop()
