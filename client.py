import socket
from udp_connection.udp_client import UDPClient
from decoder.freamereassembler import FrameReassembler
from decoder.livevideoviewer import LiveVideoViewer
from decoder.videoplaybackbuffer import VideoPlaybackBuffer
from logger.framelogmetrics import FrameLogMetrics
from logger.bufferlogger import BufferLogger

# Config
WIDTH, HEIGHT = 800, 600
FPS = 60
PAYLOAD_SIZE = 1400
BUFFER_SIZE = PAYLOAD_SIZE + 16

# Cliente UDP
client = UDPClient(port=5005, buffer_size=BUFFER_SIZE)
client.set_socket()
client.send_packet("READY")
client.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)

# Logging y ensamblador
log = FrameLogMetrics()
buffer_logger = BufferLogger(log_file="buffer.log")

reassembler = FrameReassembler(payload_size=PAYLOAD_SIZE, width=WIDTH, height=HEIGHT, logger=log)
decoder = LiveVideoViewer(width=WIDTH, height=HEIGHT)
playbackbuffer = VideoPlaybackBuffer(fps=FPS, logger=buffer_logger)

try:
    while True:
        chunk, addr = client.receive_chunk()

        # Control remoto: pausa/reanuda
        if chunk in [b'PAUSE', b'RESUME']:
            if chunk == b'PAUSE':
                print("[CLIENT] Transmisión pausada por el servidor.")
                while True:
                    ctrl_msg, _ = client.receive()
                    if ctrl_msg == b'RESUME':
                        print("[CLIENT] Transmisión reanudada por el servidor.")
                        break
                continue

        # Proceso normal
        if chunk:
            reassembler.add_chunk(chunk)

        frame = reassembler.get_next_frame()
        frame_data, _ = playbackbuffer.push_and_get(frame)

        if frame_data:
            decoder.decode_and_display(frame_data)

finally:
    decoder.release()
    buffer_logger.stop()
