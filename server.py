from udp_connection.udp_server import UDPServer
from encoder.screencapturer import ScreenCapturer
from encoder.chunker import Chunker

# Configuración

WIDTH, HEIGHT = 800, 600
FPS = 60
PAYLOAD_SIZE = 1400
BUFFER_SIZE = PAYLOAD_SIZE + 14
#BUFFER_SIZE = 65536

# Inicialización
server = UDPServer(port=5005, buffer_size=BUFFER_SIZE)
server.set_socket()
server.bind()

encoder = ScreenCapturer( width=WIDTH, height=HEIGHT, fps=FPS)
chunker = Chunker(payload_size=PAYLOAD_SIZE)

print("[SERVER] Esperando conexión del cliente...")
_, client_addr = server.receive()  # Cliente envía mensaje inicial

print(f"[SERVER] Cliente detectado: {client_addr}")
try:
    for frame in encoder:
        chunks = chunker.chunk_frame(frame)
        for chunk in chunks:
            server.send_packet_bytes(chunk, client_addr)
       
finally:
    encoder.release()


