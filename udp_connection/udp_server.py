import socket
from encoder.chunker import Chunker

class UDPServer:
    def __init__(self, host_ip='0.0.0.0', port=9999, buffer_size=1024):
        self.host_ip = host_ip
        self.port = port
        self.buffer_size = buffer_size
        self.socket = None
        #creo un objeto de tipo chunker para enviar datos
        self.chunker = Chunker(payload_size=buffer_size - 14)  # 14 bytes para el header

    def set_socket(self):
        """Crea y configura el socket UDP."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def bind(self):
        """Vincula el socket al host y puerto especificados."""
        try:
            self.socket.bind((self.host_ip, self.port))
            print(f"[SERVER] Escuchando en {self.host_ip}:{self.port}")
        except socket.error as e:
            print(f"[ERROR] No se pudo enlazar el socket: {e}")

    def receive(self):
        """Recibe un paquete de datos."""
        try:
            data, addr = self.socket.recvfrom(self.buffer_size)
            print(f"[SERVER] Recibido de {addr}: {data}")
            return data, addr
        except socket.error as e:
            print(f"[ERROR] Al recibir datos: {e}")
            return None, None

    def send_packet(self, data, addr):
        """Envía un paquete de datos a una dirección específica."""
        try:
            self.socket.sendto(data.encode(), addr)
            print(f"[SERVER] Enviado a {addr}: {data}")
        except socket.error as e:
            print(f"[ERROR] Al enviar datos: {e}")

    #funciones nuevas, para enviar chunks por frame
    def send_frame_chunks(self, frame_data, addr):
        """Divide un frame en chunks y los envía al cliente."""
        chunks = self.chunker.chunk_frame(frame_data)
        for chunk in chunks:
            self.send_packet_bytes(chunk, addr)

    #para enviarlos por bytes
    def send_packet_bytes(self, byte_data, addr):
        """Envía bytes directamente al cliente."""
        try:
            self.socket.sendto(byte_data, addr)
        except socket.error as e:
            print(f"[ERROR] Al enviar chunk: {e}")


