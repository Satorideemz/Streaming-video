import socket
import keyboard

class UDPClient:
    def __init__(self, host_ip='127.0.0.1', port=9999, buffer_size=1024):
        self.host_ip = host_ip
        self.port = port
        self.buffer_size = buffer_size
        self.socket = None

    def set_socket(self):
        """Crea el socket UDP del cliente."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_packet(self, data):
        """Envía datos al servidor."""
        try:
            self.socket.sendto(data.encode(), (self.host_ip, self.port))
            print(f"[CLIENT] Enviado a {self.host_ip}:{self.port} -> {data}")
        except socket.error as e:
            print(f"[ERROR] Al enviar datos: {e}")

    def receive(self):
        """Recibe datos del servidor."""
        try:
            data, addr = self.socket.recvfrom(self.buffer_size)
            print(f"[CLIENT] Recibido de {addr}: {data}")
            return data, addr
        except socket.error as e:
            print(f"[ERROR] Al recibir datos: {e}")
            return None, None

    #funcion en desarrollo, es para recibir chunks de informacion
    def receive_chunk(self):
        """Recibe un chunk crudo (bytes)."""
        try:
            data, addr = self.socket.recvfrom(self.buffer_size)
            print(f"[CLIENT] Chunk recibido: {len(data)} bytes, Frame ID: {int.from_bytes(data[0:2], 'big')}, Chunk ID: {int.from_bytes(data[2:4], 'big')}")
            return data, addr
        except socket.error as e:
            print(f"[ERROR] Al recibir chunk: {e}")
            return None, None

    #funciones para cerrar el servidor al apretar "q"
    def is_eof(self, data):
        """Detecta si el paquete es EOF."""
        return data[:6] == b'\xff\xff\xff\xff\xff\xff'

    def should_stop(self):
        """Detecta si el usuario presiona 'q'."""
        return keyboard.is_pressed('q')