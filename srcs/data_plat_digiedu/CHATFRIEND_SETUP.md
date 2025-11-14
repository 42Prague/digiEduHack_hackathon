# 🤖 ChatFriend Setup Guide

ChatFriend is your AI-powered qualitative analysis assistant. It uses **Ollama** to run large language models (LLMs) locally on your computer - no cloud, no API costs, complete privacy!

## ✅ What You Get

- **🔍 Semantic Search** - Find responses by meaning, not just keywords
- **🎯 Theme Extraction** - Auto-identify patterns across teacher narratives
- **⚖️ Comparative Analysis** - Compare Treatment vs Control perspectives
- **⏱️ Temporal Trends** - Track how perceptions evolve over time
- **📝 Summary Generation** - Generate comprehensive insights from qualitative data

## 📦 Installation Steps

### Step 1: Install Ollama

**macOS:**
```bash
# Download and install from website
open https://ollama.ai/download

# Or use Homebrew
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from: https://ollama.ai/download

### Step 2: Pull a Model

Once Ollama is installed, pull a language model. We recommend **llama3** (4.7GB):

```bash
ollama pull llama3
```

**Alternative models (if llama3 is too large):**
- `ollama pull mistral` (4.1GB) - Faster, still very good
- `ollama pull phi3` (2.3GB) - Smallest, good for basic tasks
- `ollama pull gemma:7b` (4.8GB) - Google's model

### Step 3: Verify Installation

Check that Ollama is running:

```bash
ollama list
```

You should see your installed model(s).

Test it:
```bash
ollama run llama3 "Hello, how are you?"
```

### Step 4: Install Python Dependencies

If you haven't already:

```bash
cd /Users/kira/42/afolder
source venv/bin/activate
pip install requests>=2.31.0
```

(This should already be in `requirements.txt`)

### Step 5: Start Using ChatFriend!

1. Make sure Ollama is running (it usually starts automatically)
2. Open your Streamlit app:
   ```bash
   streamlit run app.py
   ```
3. Navigate to **5_🤖_ChatFriend** in the sidebar
4. Start analyzing your qualitative data!

## 🎯 How to Use ChatFriend

### Semantic Search
- Enter keywords or phrases to find relevant teacher responses
- Results are ranked by relevance
- Filter by intervention status, region, or time period

### Theme Extraction
Choose between:
- **Keyword Frequency** - Fast, simple pattern detection
- **AI Analysis** - Deep thematic analysis using LLM

### Comparative Analysis
- Compare Treatment vs Control groups
- Compare different regions
- Compare different time periods
- AI identifies key differences and similarities

### Temporal Trends
- Analyze how teacher perspectives evolve over time
- Identify emerging themes at different time points
- Track intervention impact through narratives

### Summary Generation
- Generate comprehensive summaries of qualitative data
- Focus on specific topics if desired
- Export reports as text files

## 🔧 Troubleshooting

### "Ollama is not running"
```bash
# Check if Ollama service is running
curl http://localhost:11434/api/tags

# If not, start it manually (Linux)
ollama serve

# On Mac/Windows, Ollama should start automatically
```

### "No models found"
```bash
# Pull a model
ollama pull llama3

# Verify it's installed
ollama list
```

### Slow performance
- Try a smaller model: `ollama pull mistral` or `ollama pull phi3`
- Close other applications to free up RAM
- Consider using a GPU if available (Ollama auto-detects)

### API timeout errors
- Increase timeout in the code (currently set to 60 seconds)
- Use a smaller/faster model
- Reduce the amount of text being analyzed at once

## 💡 Tips for Best Results

1. **Be Specific** - The more specific your queries, the better the results
2. **Use Filters** - Narrow down to relevant subsets (Treatment only, specific region, etc.)
3. **Iterate** - Try different phrasings if you don't get good results
4. **Combine Methods** - Use keyword frequency to identify themes, then AI for deeper analysis
5. **Export Everything** - Download reports for documentation and sharing

## 📊 Model Comparison

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| llama3 | 4.7GB | Medium | Excellent | General use, best quality |
| mistral | 4.1GB | Fast | Very Good | Faster responses |
| phi3 | 2.3GB | Very Fast | Good | Limited hardware |
| gemma:7b | 4.8GB | Medium | Excellent | Alternative to llama3 |

## 🔐 Privacy & Data Security

**All data stays local!**
- No data sent to cloud servers
- No API keys needed
- No internet required (after model download)
- Your teacher responses remain completely private

## 🚀 Advanced Usage

### Using Different Models

In the ChatFriend interface, you can switch between installed models using the dropdown selector. Each model has different strengths:

- **llama3** - Best overall quality, good at nuanced analysis
- **mistral** - Faster, excellent for summaries
- **phi3** - Smallest, good for simple searches and themes

### Customizing Analysis

You can combine multiple analysis types:
1. Use **Semantic Search** to find relevant responses
2. Run **Theme Extraction** on search results
3. Generate a **Summary** focused on extracted themes
4. Export everything for your research documentation

## 📚 Learn More

- Ollama Documentation: https://github.com/ollama/ollama
- Model Library: https://ollama.ai/library
- Community Discord: https://discord.gg/ollama

---

**Need help?** Check the troubleshooting section above or consult the Ollama documentation.

**Enjoying ChatFriend?** Consider trying different models to find what works best for your analysis needs!

