from abc import ABC, abstractmethod

class AbstractTableHandler(ABC):
    @abstractmethod
    def handle(self, file_path: str) -> dict:
        pass
