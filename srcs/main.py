# from audio_to_text import audio_to_text
from read_md import read_md
from read_txt import read_txt
from read_docx import read_docx
from summary_separator import summary_separator

def main():
    # Read automated functions to automate summaries reports
    # audio_to_text()
    read_md()
    read_txt()
    read_docx()
    summary_separator()

if __name__ == "__main__":
    main()