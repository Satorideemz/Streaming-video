import time
from udp_connection.udp_server import UDPServer
from encoder.screencapturer import ScreenCapturer

WIDTH, HEIGHT = 800, 600
FPS = 60
PAYLOAD_SIZE = 1400
BUFFER_SIZE = PAYLOAD_SIZE + 16  # Cabecera actualizada a 16 bytes

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

        # 🔹 Nuevo: determinar si es keyframe y el quality_id
        is_keyframe, quality_id = encoder.is_keyframe()

        # 🔹 Enviar chunks con la nueva cabecera
        server.send_frame_chunks(frame, client_addr, quality_id, is_keyframe)

    server.send_eof(client_addr)

finally:
    encoder.release()
