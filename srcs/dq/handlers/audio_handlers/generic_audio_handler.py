from srcs.dq.handlers.audio_handlers.abstract_audio_handler import AbstractAudioHandler
from srcs.dq.summarize_mp3 import transform_to_summary


class GenericAudioHandler(AbstractAudioHandler):
    def handle(self, file_path: str) -> str:
        try:
            result_summary = transform_to_summary(file_path)
            return result_summary
        except Exception as e:
            raise RuntimeError(f"MP3 transcription failed: {file_path}, error: {e}")

    def transcribe_audio(self, audio_data: bytes) -> str:
        # Placeholder for actual transcription tool
        return "[Simulated transcripted text from MP3 audio]"
