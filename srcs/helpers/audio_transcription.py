import requests
import time

def transcribe_audio(audio_url: str) -> str:
    """
    Transcribes an audio file using AssemblyAI API.

    Args:
        audio_url (str): URL of the MP3 audio file.

    Returns:
        str: Transcribed text.
    """
    base_url = "https://api.assemblyai.com"
    headers = {
        "authorization": "6e39c034c7f3444a862e60a3245da366"
    }

    data = {
        "audio_url": audio_url,
        "language_code": "cs"
    }

    # Request transcription
    response = requests.post(f"{base_url}/v2/transcript", json=data, headers=headers)
    response.raise_for_status()  # Raise an error if request failed

    transcript_id = response.json()['id']
    polling_endpoint = f"{base_url}/v2/transcript/{transcript_id}"

    # Poll for completion
    while True:
        transcription_result = requests.get(polling_endpoint, headers=headers).json()

        if transcription_result['status'] == 'completed':
            return transcription_result['text']

        elif transcription_result['status'] == 'error':
            raise RuntimeError(f"Transcription failed: {transcription_result['error']}")

        else:
            time.sleep(3)
