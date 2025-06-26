from encoder.screencapturer import ScreenCapturer
from encoder.chunker import Chunker
from udp_connection.udp_server import UDPServer

from workers.encoder.screencapture_worker import ScreenCaptureWorker
from workers.encoder.chunker_worker import ChunkerWorker
from workers.encoder.network_sender_worker import UDPServerWorker
from workers.encoder.control_worker import ControlWorker

# Configuración
WIDTH, HEIGHT = 800, 600
FPS = 60
PAYLOAD_SIZE = 1400
BUFFER_SIZE = PAYLOAD_SIZE + 16

# Instancias
screen_capturer = ScreenCapturer(width=WIDTH, height=HEIGHT, fps=FPS)
screen_worker = ScreenCaptureWorker(screen_capturer)

chunker = Chunker(payload_size=PAYLOAD_SIZE)
chunker_worker = ChunkerWorker(chunker)

udp_server = UDPServer(port=5005, buffer_size=BUFFER_SIZE)
udp_worker = UDPServerWorker(udp_server)

# Control principal
workers = {
    "screen": screen_worker,
    "chunker": chunker_worker,
    "udp": udp_worker
}

control = ControlWorker(
    workers=workers,
    udp_server=udp_server,
    screen_capturer=screen_capturer
)

# Lanzador simple
if __name__ == "__main__":
    try:
        control.start()
        control.main_thread.join()  # Espera a que finalice el ciclo principal
    except KeyboardInterrupt:
        print("[MAIN] Interrupción manual detectada.")
    finally:
        control.stop()
