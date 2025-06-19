from udp_connection.udp_server import UDPServer
from encoder.screencapturer import ScreenCapturer
from config_loader import ConfigManager


config_manager = ConfigManager(config_files=["config1.json", "config2.json"], switch_interval=10)

WIDTH = config_manager.get("WIDTH")
HEIGHT = config_manager.get("HEIGHT")
FPS = config_manager.get("FPS")
PAYLOAD_SIZE = config_manager.get("PAYLOAD_SIZE")
PORT = config_manager.get("PORT")

BUFFER_SIZE = PAYLOAD_SIZE + 14

server = UDPServer(port=5005, buffer_size=BUFFER_SIZE)
server.set_socket()
server.bind()

encoder = ScreenCapturer(width=WIDTH, height=HEIGHT, fps=FPS)

print("[SERVER] Esperando conexión del cliente...")
_, client_addr = server.receive()
print(f"[SERVER] Cliente detectado: {client_addr}")

try:
    last_width = config_manager.get("WIDTH")
    last_height = config_manager.get("HEIGHT")
    last_fps = config_manager.get("FPS")

    for frame in encoder:
        server.toggle_pause(client_addr)

        if server.should_stop():
            print("[SERVER] 'q' presionado. Finalizando transmisión.")
            break

        if server.is_paused():
            continue # No enviamos el frame actual, lo descartamos

        # Revisar si hay cambios en configuración
        new_width = config_manager.get("WIDTH")
        new_height = config_manager.get("HEIGHT")
        new_fps = config_manager.get("FPS")

        if (new_width, new_height, new_fps) != (last_width, last_height, last_fps):
            encoder.update_config(new_width, new_height, new_fps)
            last_width, last_height, last_fps = new_width, new_height, new_fps

        server.send_frame_chunks(frame, client_addr)

    server.send_eof(client_addr)

finally:
    encoder.release()
    config_manager.stop()
