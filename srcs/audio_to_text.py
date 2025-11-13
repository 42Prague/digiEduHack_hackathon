import pandas as pd
import numpy as np
import librosa
import glob
import os
import torch
from faster_whisper import WhisperModel

def audio_to_text(str: folder_path):
    """
    Finds audio files (.wav, .mp3, .flac, .ogg, .m4a, upper or lowercase) in a folder,
    loads a medium WhisperModel, and writes plain text transcripts in a 'transcripts' folder.
    GPU is used automatically if available.
    """

    # List of common audio extensions
    audio_exts = ["wav", "mp3", "flac", "ogg", "m4a"]

    # Collect all audio files
    audio_files = []
    for ext in audio_exts:
        audio_files.extend(glob.glob(os.path.join(folder_path, f"*.{ext}")))
        audio_files.extend(glob.glob(os.path.join(folder_path, f"*.{ext.upper()}")))  # handle uppercase

    print(f"Found {len(audio_files)} audio files.")

    # --- Output folder for transcripts ---
    output_folder = os.path.join(folder_path, "transcripts")
    os.makedirs(output_folder, exist_ok=True)

    # --- Detect device ---
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # --- Load Whisper model ---
    model = WhisperModel("medium", device=device)

    # --- Transcribe only files without existing transcript ---
    for audio_path in audio_files:
        filename = os.path.basename(audio_path)
        txt_filename = os.path.splitext(filename)[0] + ".txt"
        txt_path = os.path.join(output_folder, txt_filename)

        if os.path.exists(txt_path):
            print(f"Skipping {filename}, transcript already exists.")
            continue

        print(f"Transcribing {filename}...")

        segments, info = model.transcribe(audio_path)

        # Combine segments into a single transcript
        transcript_text = ""
        for segment in segments:
            start = f"{segment.start:.2f}s"
            end = f"{segment.end:.2f}s"
            transcript_text += f"[{start} -> {end}] {segment.text}\n"

        # Save transcript to a text file
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)

        print(f"Saved transcript to {txt_path}")

    print("All missing audio transcripts have been generated.")