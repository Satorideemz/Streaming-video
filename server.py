from udp_connection.udp_server import UDPServer
from encoder.screencapturer import ScreenCapturer

WIDTH, HEIGHT = 800, 600
FPS = 60
PAYLOAD_SIZE = 1400
BUFFER_SIZE = PAYLOAD_SIZE + 14

server = UDPServer(port=5005, buffer_size=BUFFER_SIZE)
server.set_socket()
server.bind()

encoder = ScreenCapturer(width=WIDTH, height=HEIGHT, fps=FPS)

print("[SERVER] Esperando conexión del cliente...")
_, client_addr = server.receive()
print(f"[SERVER] Cliente detectado: {client_addr}")

try:

    for frame in encoder:
        server.toggle_pause(client_addr)

        if server.should_stop():
            print("[SERVER] 'q' presionado. Finalizando transmisión.")
            break

        if server.is_paused():
            continue  # No enviamos el frame actual, lo descartamos

        server.send_frame_chunks(frame, client_addr)

    server.send_eof(client_addr)

finally:
    encoder.release()


