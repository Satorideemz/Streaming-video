import threading
import queue
import socket
from typing import Optional
from udp_connection.udp_client import UDPClient
import time

class UDPReceiverWorker:
    """
    Encapsula el manejo de un cliente UDP en un hilo separado.
    Recibe paquetes (chunks) y los encola para ser procesados por el hilo principal.
    """
    def __init__(self, udp_client: UDPClient, max_queue_size: int = 2400):
        self.client = udp_client
        self.packet_queue = queue.Queue(maxsize=max_queue_size)
        self.running = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.stop_event = threading.Event()  # alternativa al flag bool si se desea más control

    def start(self):
        """Inicia el hilo receptor."""
        if not self.running:
            self.running = True
            self.thread.start()
            print("[UDP RECEIVER] Hilo iniciado.")

    def stop(self):
        """Detiene el hilo receptor de forma segura."""
        self.running = False
        self.stop_event.set()
        self.thread.join()
        print("[UDP RECEIVER] Hilo detenido.")

    def should_stop(self) -> bool:
        """Consulta si se ha presionado la tecla de parada."""
        return self.client.should_stop()

    def get_next_packet(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """
        Devuelve el próximo paquete recibido (si hay alguno).
        :param timeout: Tiempo máximo de espera para obtener el paquete.
        :return: Bytes del paquete o None si no hay disponible.
        """
        #time.sleep(0.028)
        try:
            return self.packet_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _run(self):
        """Loop principal del hilo, recibe y encola paquetes UDP."""
        print("[UDP RECEIVER] Loop de recepción iniciado.")
        while self.running and not self.stop_event.is_set():
 
            try:
                chunk, addr = self.client.receive_chunk()

                if chunk is None:
                    continue

                # EOF manual por paquete especial
                if self.client.is_eof(chunk):
                    print("[UDP RECEIVER] Paquete EOF detectado, cerrando hilo.")
                    self.running = False
                    break

                try:
                    self.packet_queue.put(chunk, timeout=0.1)
                    #print(f"[UDP RECEIVER] Chunk recibido ({len(chunk)} bytes), encolado.")
                except queue.Full:
                    print("[UDP RECEIVER] Cola llena. Paquete descartado.")

            except socket.error as e:
                print(f"[UDP RECEIVER] Error de socket: {e}")
