import socket
from udp_connection.udp_client import UDPClient
from decoder.freamereassembler import FrameReassembler
from decoder.livevideoviewer import LiveVideoViewer
from framelogmetrics import FrameLogMetrics
from config_loader import ConfigManager

config_manager = ConfigManager(config_files=["config1.json", "config2.json"], switch_interval=10)

WIDTH = config_manager.get("WIDTH")
HEIGHT = config_manager.get("HEIGHT")
FPS = config_manager.get("FPS")
PAYLOAD_SIZE = config_manager.get("PAYLOAD_SIZE")
PORT = config_manager.get("PORT")


BUFFER_SIZE = PAYLOAD_SIZE + 14

client = UDPClient(port=5005, buffer_size=BUFFER_SIZE)
client.set_socket()
client.send_packet("READY")
client.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64 * 1024 * 1024)

log = FrameLogMetrics()
reassembler = FrameReassembler(payload_size=PAYLOAD_SIZE, width=WIDTH, height=HEIGHT, logger=log)
decoder = LiveVideoViewer(width=WIDTH, height=HEIGHT, fps=FPS)


try:
    last_width = config_manager.get("WIDTH")
    last_height = config_manager.get("HEIGHT")
    last_fps = config_manager.get("FPS")

    while True:
        chunk, addr = client.receive_chunk()
        #funcion de cierre desde el servidor inestable, quitado temporalmente
        # if client.should_stop():
        #     print("[CLIENT] 'q' presionado. Finalizando recepción.")
        #     break

        # chunk, addr = client.receive_chunk()
        # if chunk:
        #     if client.is_eof(chunk):
        #         print("[CLIENT] Fin de transmisión detectado.")
        #         break
            
        # Verificamos si es un mensaje de control como PAUSE o RESUME
        # Verificamos si es un mensaje de control como PAUSE o RESUME
        if chunk in [b'PAUSE', b'RESUME']:
            if chunk == b'PAUSE':
                print("[CLIENT] Transmisión pausada por el servidor.")
                # Esperamos hasta recibir un RESUME
                while True:
                    ctrl_msg, _ = client.receive()
                    if ctrl_msg == b'RESUME':
                        print("[CLIENT] Transmisión reanudada por el servidor.")
                        break
                continue # Vuelve al bucle principal

        # Verificar cambios de configuración
        new_width = config_manager.get("WIDTH")
        new_height = config_manager.get("HEIGHT")
        new_fps = config_manager.get("FPS")

        if (new_width, new_height) != (last_width, last_height):
            reassembler.update_config(new_width, new_height)
        if (new_width, new_height, new_fps) != (last_width, last_height, last_fps):
            decoder.update_config(new_width, new_height, new_fps)
            
        # Si era RESUME directamente, no hacemos nada y seguimos
        last_width, last_height, last_fps = new_width, new_height, new_fps

        # Procesamiento normal
        if chunk:
            reassembler.add_chunk(chunk)

        frame_bytes = reassembler.get_next_frame()
        if frame_bytes:
            decoder.decode_and_display(frame_bytes)

finally:
    decoder.release()
    config_manager.stop()
