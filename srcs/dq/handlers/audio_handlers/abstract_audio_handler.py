from abc import ABC, abstractmethod

class AbstractAudioHandler(ABC):

    @abstractmethod
    def handle(self, file_path: str) -> str:
        pass