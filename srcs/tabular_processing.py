import pandas as pd
import pyarrow as pa
import requests

def data_preprocessing(file_path):
    col_names = pd.read_excel(file_path, nrows=0).iloc[:0]
    # col_names.info()

    prompt = [
    "Simplify survey questions.",
    "Rename columns",
    "Rules: 'keep meaning', 'still understandable', "
    "use underscore instead of spaces, don't use any extra symbols, keep everything."
    ]



    response = requests.post(
        "https://localhost:11434/api/generate",
        json={"model":"ollama3.1", "prompt":prompt, "stream": False},
        verify=False
    )
    result = response.json().get("response")
    print(result)

def main():
    data_preprocessing(file_path=
                       "/home/chowmein/hackathon_project/data_samples_eduzmena/Data samples/ZV Otevirame dvere kolegialni podpore_běh 1_12 2023 (Odpovědi).xlsx")

if __name__ == "__main__":
    main()
    