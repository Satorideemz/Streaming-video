import socket
from udp_connection.udp_client import UDPClient
from decoder.freamereassembler import FrameReassembler
from decoder.livevideoviewer import LiveVideoViewer
from framelogmetrics import FrameLogMetrics

WIDTH, HEIGHT = 800, 600
FPS = 100
PAYLOAD_SIZE = 1400
BUFFER_SIZE = PAYLOAD_SIZE + 14

client = UDPClient(port=5005, buffer_size=BUFFER_SIZE)
client.set_socket()
client.send_packet("READY")
client.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)

log = FrameLogMetrics()
reassembler = FrameReassembler(payload_size=PAYLOAD_SIZE, width=WIDTH, height=HEIGHT, logger=log)
decoder = LiveVideoViewer(width=WIDTH, height=HEIGHT, fps=FPS)

try:
    while True:
        if client.should_stop():
            print("[CLIENT] 'q' presionado. Finalizando recepción.")
            break

        chunk, addr = client.receive_chunk()
        if chunk:
            if client.is_eof(chunk):
                print("[CLIENT] Fin de transmisión detectado.")
                break

            reassembler.add_chunk(chunk)

        frame_bytes = reassembler.get_next_frame()
        if frame_bytes:
            decoder.decode_and_display(frame_bytes)

finally:
    decoder.release()
