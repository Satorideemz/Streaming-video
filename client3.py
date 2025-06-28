import socket
import queue
from udp_connection.udp_client import UDPClient
from decoder.freamereassembler import FrameReassembler
from decoder.livevideoviewer import LiveVideoViewer
from decoder.videoplaybackbuffer import VideoPlaybackBuffer
from logger.framelogmetrics import FrameLogMetrics
from logger.bufferlogger import BufferLogger
from workers.decoder.framereassembler_worker import FrameReassemblerWorker

from workers.decoder.network_receiver_worker import UDPReceiverWorker

# Config
WIDTH, HEIGHT = 800, 600
FPS = 30
PAYLOAD_SIZE = 1400
BUFFER_SIZE = PAYLOAD_SIZE + 16

# Crear el cliente y worker
client = UDPClient(port=5005, buffer_size=BUFFER_SIZE)
client.set_socket()
client.send_packet("READY")
client.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)

receiver_worker = UDPReceiverWorker(udp_client=client, max_queue_size=1800)
receiver_worker.start()

# Logging y ensamblador
log = FrameLogMetrics()
buffer_logger = BufferLogger(log_file="buffer.log")

reassembler = FrameReassembler(payload_size=PAYLOAD_SIZE, width=WIDTH, height=HEIGHT, logger=log)
decoder = LiveVideoViewer(width=WIDTH, height=HEIGHT)
playbackbuffer = VideoPlaybackBuffer(fps=FPS, logger=buffer_logger)

# Colas
chunk_queue = receiver_worker.packet_queue
frame_queue = queue.Queue(maxsize=40)

# Crear reassembler worker
reassembler_worker = FrameReassemblerWorker(
    reassembler=reassembler,
    input_queue=chunk_queue,
    output_queue=frame_queue
)
reassembler_worker.start()

try:
    while True:
        if receiver_worker.should_stop():
            break

        frame = reassembler_worker.get_next_frame(timeout=1.0)
        if not frame:
            continue

        frame_data, _ = playbackbuffer.push_and_get(frame)
        if frame_data:
            decoder.decode_and_display(frame_data)

finally:
    receiver_worker.stop()
    reassembler_worker.stop()
    decoder.release()
    buffer_logger.stop()

