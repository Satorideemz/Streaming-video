import threading
import keyboard
import time

class ControlWorker:
    """
    Controlador maestro que:
    - Maneja la pausa y la salida con teclas ('p' y 'q')
    - Orquesta los hilos de captura, chunking y UDP
    - Ejecuta el bucle principal de transmisión
    """
    def __init__(self, workers: dict, udp_server, screen_capturer):
        self.workers = workers  # {'screen': ..., 'chunker': ..., 'udp': ...}
        self.udp_server = udp_server
        self.screen_capturer = screen_capturer

        self.paused = False
        self.should_exit = False
        self.client_addr = None

        self.lock = threading.Lock()
        self.key_thread = threading.Thread(target=self._listen_keys, daemon=True)
        self.main_thread = threading.Thread(target=self._run_loop, daemon=True)

    def start(self):
        print("[CONTROL] Iniciando hilos de trabajo...")
        for name, worker in self.workers.items():
            print(f"[CONTROL] → Iniciando '{name}'")
            worker.start()

        print("[CONTROL] Esperando conexión de cliente UDP...")
        while self.client_addr is None:
            self.client_addr = self.workers["udp"].get_client_addr()
            time.sleep(0.05)

        print(f"[CONTROL] Cliente conectado desde: {self.client_addr}")
        self.key_thread.start()
        self.main_thread.start()

    def stop(self):
        print("[CONTROL] Deteniendo todos los hilos...")
        self.should_exit = True
        self.main_thread.join()
        self.key_thread.join()

        for name, worker in self.workers.items():
            print(f"[CONTROL] → Deteniendo '{name}'")
            worker.stop()

        self.screen_capturer.release()
        if self.client_addr:
            self.udp_server.send_eof(self.client_addr)

        print("[CONTROL] Todos los hilos detenidos. Servidor finalizado.")

    def _listen_keys(self):
        """Escucha las teclas 'p' (pausa) y 'q' (salir)."""
        print("[CONTROL] Escuchando teclas 'p' (pausar) y 'q' (salir)...")
        while not self.should_exit:
            if keyboard.is_pressed('p'):
                with self.lock:
                    self.paused = not self.paused
                    estado = "PAUSADO" if self.paused else "REANUDADO"
                    print(f"[CONTROL] Estado de transmisión: {estado}")
                while keyboard.is_pressed('p'):
                    time.sleep(0.2)  # Debounce

            if keyboard.is_pressed('q'):
                with self.lock:
                    self.should_exit = True
                    print("[CONTROL] 'q' presionado. Señalando cierre...")
                break
            time.sleep(0.1)  # ← Esto es clave para que no monopolice la CPU
    def _run_loop(self):
        """Bucle principal de transmisión de frames."""
        screen = self.workers["screen"]
        chunker = self.workers["chunker"]

        print("[CONTROL] Comenzando bucle principal de transmisión...")
        while not self.should_exit:
            with self.lock:
                if self.paused:
                    time.sleep(0.1)
                    continue

            frame = screen.get_latest_frame()
            if frame is None:
           
                continue

            is_keyframe, quality_id = screen.is_keyframe()
            chunker.enqueue_frame(frame, quality_id, is_keyframe)

            fps=screen.get_fps()
            chunk_data = chunker.get_latest_chunks(fps)
            if chunk_data is None:

                continue

            for chunk in chunk_data["chunks"]:
                self.udp_server.send_packet_bytes(chunk, self.client_addr)
