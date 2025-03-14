import mmap
import threading
import logging

logger = logging.getLogger(__name__)


class RingBuffer:
    def __init__(self, size: int):
        self.size = size
        self.buf = mmap.mmap(-1, size)
        self.lock = threading.Lock()
        self.head = 0
        self.tail = 0
        self.overwrites = 0  # Track the number of overwrites

    def write(self, data: bytes) -> None:
        with self.lock:
            if len(data) > self.size:
                raise ValueError("Data too large for buffer.")
            for byte in data:
                next_head = (self.head + 1) % self.size
                # If next_head == self.tail, that means the buffer was full
                # before writing this byte
                if next_head == self.tail:
                    self.tail = (self.tail + 1) % self.size
                    self.overwrites += 1
                    if self.overwrites % 100 == 0:
                        logger.warning(
                            "RingBuffer: Data overwritten (overwrites: %d)",
                            self.overwrites,
                        )
                self.buf[self.head] = byte
                self.head = next_head

    def read(self, length: int) -> bytes:
        with self.lock:
            available = (self.head - self.tail) % self.size
            if length > available:
                # If requesting more than available, pad with zeros
                data = bytearray()
                for _ in range(available):
                    data.append(self.buf[self.tail])
                    self.tail = (self.tail + 1) % self.size
                # Pad remaining length with zeros
                data.extend([0] * (length - available))
                return bytes(data)
            data = bytearray()
            for _ in range(length):
                data.append(self.buf[self.tail])
                self.tail = (self.tail + 1) % self.size
            return bytes(data)
