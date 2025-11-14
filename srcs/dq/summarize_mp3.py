import json
import os
import tempfile

import ffmpeg
from vosk import KaldiRecognizer, Model

from srcs.dq.agent import call_agent, prompt

# -------------------------------
#  VOSK MODEL
# -------------------------------

# VOSK_MODEL_PATH = "vosk-model-small-cs-0.4-rhasspy"
VOSK_MODEL_PATH = "srcs/dq/vosk-model-small-cs-0.4-rhasspy"
model = Model(VOSK_MODEL_PATH)


# -------------------------------
#  AUDIO → WAV CONVERSION
# -------------------------------
def convert_to_wav(input_path: str, sample_rate: int = 16000) -> str:
    fd, tmp_wav_path = tempfile.mkstemp(suffix=".wav")

    os.close(fd)
    (
        ffmpeg.input(input_path)
        .output(tmp_wav_path, ac=1, ar=sample_rate, format="wav")
        .overwrite_output()
        .run(quiet=True)
    )
    return tmp_wav_path


# -------------------------------
#  TRANSCRIBE WITH VOSK
# -------------------------------
def transcribe_audio(path: str) -> str:
    wav_path = convert_to_wav(path)

    try:
        rec = KaldiRecognizer(model, 16000)
        rec.SetWords(True)

        transcript_chunks = []

        with open(wav_path, "rb") as wf:
            while True:
                data = wf.read(4000)
                if not data:
                    break
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    transcript_chunks.append(res.get("text", ""))

            final_res = json.loads(rec.FinalResult())
            transcript_chunks.append(final_res.get("text", ""))

        return " ".join(transcript_chunks).strip()

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


def clean_czech_text(text: str) -> str:
    return text.replace("[unk]", "").strip()


# -------------------------------
#  SUMMARIZATION VIA LLAMA
# -------------------------------


def transform_to_summary(path: str):
    transcript = transcribe_audio(path)
    cleaned = clean_czech_text(transcript)
    summary = call_agent(prompt, cleaned)

    return summary
