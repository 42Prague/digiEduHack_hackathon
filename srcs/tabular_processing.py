
import requests
import json
import os
import argparse
from pathlib import Path

def data_preprocessing(file_path, output_json="output.json"):
    # import python-docx lazily to avoid import-time failures when an incompatible
    # `docx` package is installed system-wide.
    try:
        from docx import Document
    except Exception as e:
        raise ImportError(
            "python-docx is required to process .docx files. "
            "If you have a package named `docx` installed, uninstall it and install `python-docx`:\n"
            "python3 -m pip uninstall docx\npython3 -m pip install python-docx"
        ) from e

    doc = Document(file_path)
    full_text = "\n".join([p.text for p in doc.paragraphs])

    # Create the prompt: ask the model for a concise plain-text summary only.
    # We will wrap that summary into a simple JSON ourselves to avoid enforcing
    # specific keys coming from the model.
    prompt = f'''
    Provide a short, neutral summary (2-6 sentences) of the text below. 
    Do not return JSON — return only plain text (the summary).

    Text:
    {full_text}
    '''

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model":"gemma2:9b", "prompt":prompt, "stream": False},
    )
    # model response is expected to be plain text summary
    summary_text = response.json().get('response', '')

    # Wrap into a simple unstructured JSON (single 'text' key) to avoid using
    # the keys 'topics','entities','facts'. This matches the user's request.
    data = summary_text_to_json(summary_text, output_json=output_json, structured=False)

    print(f"JSON saved to {output_json}")
    return data


def summary_text_to_json(summary_text, output_json=None, structured=False):
    """Create JSON from a plain text summary.

    By default (structured=False) this returns an unstructured JSON with a single
    key `text` containing the original text. If structured=True, returns the
    lightweight structured form with keys 'topics','entities','facts' (backwards compatible).
    """
    if structured:
        data = {
            "topics": [],
            "entities": [],
            "facts": [summary_text.strip()] if summary_text and summary_text.strip() else [],
        }
    else:
        data = {
            "text": summary_text or ""
        }
    if output_json:
        os.makedirs(os.path.dirname(output_json) or '.', exist_ok=True)
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    return data


def batch_generate_json(input_path, output_dir):
    """Process a file or directory and generate JSONs for .docx and .txt files.

    For .docx files, uses `data_preprocessing`. For .txt files, wraps text using
    `summary_text_to_json`.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = []
    if input_path.is_dir():
        files = list(input_path.glob('**/*'))
    else:
        files = [input_path]

    results = []
    for f in files:
        if f.is_dir():
            continue
        if f.suffix.lower() == '.docx':
            out = output_dir / (f.stem + '.json')
            try:
                data = data_preprocessing(str(f), output_json=str(out))
                results.append((str(f), str(out), 'ok'))
            except Exception as e:
                results.append((str(f), None, f'error: {e}'))
        elif f.suffix.lower() in {'.txt', '.md'}:
            out = output_dir / (f.stem + '.json')
            text = f.read_text(encoding='utf-8')
            data = summary_text_to_json(text, output_json=str(out), structured=False)
            results.append((str(f), str(out), 'ok'))
        else:
            # skip other file types
            continue

    return results


def _cli():
    parser = argparse.ArgumentParser(description='Batch-generate JSON summaries from .docx or .txt files')
    parser.add_argument('--input', '-i', required=True, help='Input file or directory')
    parser.add_argument('--output-dir', '-o', default='json_outputs', help='Directory to write JSON files')
    args = parser.parse_args()
    res = batch_generate_json(args.input, args.output_dir)
    for src, out, status in res:
        print(src, '->', out, status)

def main():
    insights = data_preprocessing(file_path=
        "/home/sofiemeyer/Projects/hackathon/data_samples_eduzmena/Data samples/Prepis_FG_PedagogLidr_mentori.docx",
        output_json="output.json")
    print(insights)
    

if __name__ == "__main__":
    main()
    