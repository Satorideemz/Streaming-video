import threading
from typing import Optional, Tuple
from udp_connection.udp_server import UDPServer


class UDPServerWorker:
    """
    Encapsula el manejo de un servidor UDP en un hilo separado.
    """
    def __init__(self, udp_server: UDPServer):
        self.server = udp_server
        self.client_addr: Optional[Tuple[str, int]] = None
        self.running = False
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.server.set_socket()
        self.server.bind()
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def is_paused(self):
        return self.server.is_paused()

    def should_stop(self):
        return self.server.should_stop()

    def get_client_addr(self) -> Optional[Tuple[str, int]]:
        return self.client_addr

    def _run(self):
        print("[UDP WORKER] Esperando conexión del cliente...")
        data, addr = self.server.receive()
        if addr:
            self.client_addr = addr
            print(f"[UDP WORKER] Cliente detectado: {addr}")
        else:
            print("[UDP WORKER] No se pudo establecer cliente.")
