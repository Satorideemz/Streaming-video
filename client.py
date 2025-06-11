import socket
from udp_connection.udp_client import UDPClient
from decoder.freamereassembler import FrameReassembler
from decoder.livevideoviewer import LiveVideoViewer
from framelogmetrics import FrameLogMetrics

# Configuración

WIDTH, HEIGHT =  800, 600
FPS = 100
PAYLOAD_SIZE = 1400
BUFFER_SIZE = PAYLOAD_SIZE + 14
#BUFFER_SIZE = 65536

# Inicialización
client = UDPClient(port=5005, buffer_size=BUFFER_SIZE)
client.set_socket()
client.send_packet("READY")  # Solicitud inicial al servidor
client.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)  # 4 MB

log = FrameLogMetrics()
reassembler = FrameReassembler(payload_size=PAYLOAD_SIZE, width=WIDTH, height=HEIGHT,logger=log)

decoder = LiveVideoViewer ( width=WIDTH, height=HEIGHT, fps=FPS)

try:
    while True:
        chunk, addr = client.receive_chunk()
        if chunk:
            reassembler.add_chunk(chunk)

        frame_bytes = reassembler.get_next_frame()
        if frame_bytes:
            decoder.decode_and_display(frame_bytes)

finally:
    decoder.release()