import time

from udp_connection.udp_server import UDPServer
from encoder.screencapturer import ScreenCapturer
from workers.encoder.screencapture_worker import ScreenCaptureWorker  # ⬅️ nuevo

WIDTH, HEIGHT = 800, 600
FPS = 60
PAYLOAD_SIZE = 1400
BUFFER_SIZE = PAYLOAD_SIZE + 16  # Cabecera actualizada a 16 bytes

server = UDPServer(port=5005, buffer_size=BUFFER_SIZE)
server.set_socket()
server.bind()

# ⬇️ Instanciar ScreenCapturer y Worker
capturer = ScreenCapturer(width=WIDTH, height=HEIGHT, fps=FPS)
worker = ScreenCaptureWorker(capturer)
worker.start()  # ⬅️ arranca el hilo de captura

print("[SERVER] Esperando conexión del cliente...")
_, client_addr = server.receive()
print(f"[SERVER] Cliente detectado: {client_addr}")

try:
    while True:
        server.toggle_pause(client_addr)

        if server.should_stop():
            print("[SERVER] 'q' presionado. Finalizando transmisión.")
            break

        if server.is_paused():
            continue

        # ⬇️ Obtener el último frame disponible del buffer
        frame = worker.get_latest_frame()
        if frame is None:
            continue  # Nada disponible todavía

        is_keyframe, quality_id = worker.is_keyframe()
        server.send_frame_chunks(frame, client_addr, quality_id, is_keyframe)
        
    server.send_eof(client_addr)

finally:
    worker.stop()
