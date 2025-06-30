import threading
import queue
from typing import Optional
from decoder.freamereassembler import FrameReassembler
import time

class FrameReassemblerWorker:
    """
    Worker que se encarga de ensamblar frames a partir de los chunks entrantes.
    Corre en un hilo separado, consumiendo desde una cola de chunks y
    produciendo una cola de frames listos para ser decodificados.
    """
    def __init__(self, reassembler: FrameReassembler,
                 input_queue: queue.Queue,
                 output_queue: Optional[queue.Queue] = None,
                 max_output_size: int = 60):

        self.reassembler = reassembler
        self.input_queue = input_queue
        self.output_queue = output_queue or queue.Queue(maxsize=max_output_size)

        self.running = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.stop_event = threading.Event()

    def start(self):
        """Inicia el hilo de ensamblado."""
        if not self.running:
            self.running = True
            self.thread.start()
            print("[REASSEMBLER WORKER] Hilo iniciado.")

    def stop(self):
        """Detiene el hilo de forma segura."""
        self.running = False
        self.stop_event.set()
        self.thread.join()
        print("[REASSEMBLER WORKER] Hilo detenido.")

    def get_next_frame(self, timeout: Optional[float] = None):
        """Obtiene el siguiente frame ensamblado desde la cola de salida."""
        #time.sleep(0.03)
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _run(self):
        """Loop principal de ensamblado."""
        print("[REASSEMBLER WORKER] Loop de ensamblado iniciado.")
        while self.running and not self.stop_event.is_set():
            
            try:
                # Intentar obtener chunk
                chunk = self.input_queue.get(timeout=0.1)
                if chunk:
                    self.reassembler.add_chunk(chunk)
                    
                    # Armar todos los frames posibles
                    while True:
                        
                        frame = self.reassembler.get_next_frame()
                        if frame is None:
                            break
                        try:
                            self.output_queue.put(frame, timeout=0.1)
                            #print(f"[REASSEMBLER WORKER] Frame encolado: ID {frame['frame_id']}")
                        except queue.Full:
                            print("[REASSEMBLER WORKER] Cola de frames llena, frame descartado.")
            except queue.Empty:
                continue
