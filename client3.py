import socket
import queue
from udp_connection.udp_client import UDPClient
from decoder.freamereassembler import FrameReassembler
from decoder.livevideoviewer import LiveVideoViewer
from decoder.videoplaybackbuffer import VideoPlaybackBuffer
from logger.framelogmetrics import FrameLogMetrics
from logger.bufferlogger import BufferLogger

from workers.decoder.network_receiver_worker import UDPReceiverWorker

# Config
WIDTH, HEIGHT = 800, 600
FPS = 75
PAYLOAD_SIZE = 1400
BUFFER_SIZE = PAYLOAD_SIZE + 16

# Crear el cliente y worker
client = UDPClient(port=5005, buffer_size=BUFFER_SIZE)
client.set_socket()
client.send_packet("READY")
client.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)

receiver_worker = UDPReceiverWorker(udp_client=client, max_queue_size=2400)
receiver_worker.start()


# Logging y ensamblador
log = FrameLogMetrics()
buffer_logger = BufferLogger(log_file="buffer.log")

reassembler = FrameReassembler(payload_size=PAYLOAD_SIZE, width=WIDTH, height=HEIGHT, logger=log)
decoder = LiveVideoViewer(width=WIDTH, height=HEIGHT)
playbackbuffer = VideoPlaybackBuffer(fps=FPS, logger=buffer_logger)


from workers.decoder.framereassembler_worker import FrameReassemblerWorker

# Colas
chunk_queue = receiver_worker.packet_queue
frame_queue = queue.Queue(maxsize=60)

# Crear reassembler worker
reassembler_worker = FrameReassemblerWorker(
    reassembler=reassembler,
    input_queue=chunk_queue,
    output_queue=frame_queue
)
reassembler_worker.start()


from workers.decoder.videoplaybackbuffer_worker import VideoPlaybackBufferWorker

frame_queue = reassembler_worker.output_queue  # Ya existente
playback_queue = queue.Queue(maxsize=60)       # Para frames listos a mostrar

playback_worker = VideoPlaybackBufferWorker(
    video_buffer=playbackbuffer,
    input_queue=frame_queue,
    output_queue=playback_queue
)
playback_worker.start()


try:
    while True:
        if receiver_worker.should_stop():
            break

        result = playback_worker.get_next_decoded_frame(timeout=1.0)
        if result is None:
            continue

        frame_data, metadata = result
        decoder.decode_and_display(frame_data)

finally:
    receiver_worker.stop()
    reassembler_worker.stop()
    playback_worker.stop()
    decoder.release()
    buffer_logger.stop()
