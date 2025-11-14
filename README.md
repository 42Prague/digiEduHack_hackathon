# Hackathon RAG System with Multi-LLM Support

## 1. One-sentence description
A retrieval-augmented generation (RAG) system that ingests documents, indexes chunks, and answers questions or generates structured data using multiple LLMs, Architecture based on TimeServiceDB structure.

## 2. Technology stack
- **Backend:** Python 3.11, Flask  
- **Frontend:** Vite, React, TypeScript, TailwindCSS  
- **Key Libraries (Backend):** `openai`, `pdfplumber`, `mammoth`, `markdown`, `requests`, `BeautifulSoup`  
- **Key Libraries (Frontend):** `lucide-react`, `sonner`, custom UI components (Card, Button, Input, Select, Textarea)  
- **AI Models Used:** Llama 3.3 70B Instruct via Featherless API the model can be Self-hosted.
- 
## 3. Data Privacy Statement
- **Where data is processed:** EU-based cloud (Featherless AI EU endpoints)/local hosting possibility
- **AI services used:** Self-hosted Llama 3  
- **Does data leave the EU?:** No, all user data remains within EU servers/within internal company servers 

## 4. Monthly cost estimate
€50–€250 depending on usage and API calls  

## 5. Prerequisites
- Python 3.11  
- Node.js 20+  
- `FEATHERLESS_API_KEY` environment variable  

## 6. Setup instructions

# Backend setup
# Clone the repo
git clone https://github.com/yourusername/hackathon-rag.git
cd hackathon-rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set Featherless API key
export FEATHERLESS_API_KEY="your_api_key_here"  # Linux/macOS
set FEATHERLESS_API_KEY="your_api_key_here"     # Windows


# Frontend setup
cd frontend
npm install
npm run dev


## 7. How to run locally
python -m your_package.app
npm run dev

## 8.How to deploy to production
Containerize the application using Docker
docker build -t hackathon-rag .
docker run -e FEATHERLESS_API_KEY="your_api_key_here" -p 5000:5000 hackathon-rag

## 9. Known limitations

Only supports text-based PDF, DOCX, Markdown, and MP3 transcriptions

Region filtering may fail if metadata is missing or malformed

LLM responses are limited to 1–3 sentences or JSON strictly; no reasoning is included

Large documents may exceed token limits for Featherless API