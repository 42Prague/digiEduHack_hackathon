# 🤖 ChatFriend Setup Guide

ChatFriend is your AI-powered qualitative analysis assistant. It uses **Hugging Face's cloud-based LLM API** to provide powerful AI analysis capabilities through a simple, containerized service.

## ✅ What You Get

- **🔍 Semantic Search** - Find responses by meaning, not just keywords
- **🎯 Theme Extraction** - Auto-identify patterns across teacher narratives
- **⚖️ Comparative Analysis** - Compare Treatment vs Control perspectives
- **⏱️ Temporal Trends** - Track how perceptions evolve over time
- **📝 Summary Generation** - Generate comprehensive insights from qualitative data

## 📦 Installation Steps

### Step 1: Get a Hugging Face API Key

1. Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Create a new token (Read role is sufficient)
3. Copy the token

### Step 2: Configure Environment Variables

1. Navigate to the project directory:
   ```bash
   cd /Users/kira/fuckk/srcs/data_plat_digiedu
   ```

2. Edit the `.env` file and add your API key:
   ```bash
   # Open the .env file
   nano .env
   
   # Replace 'your_huggingface_api_key_here' with your actual token
   HF_API_KEY=hf_YourActualTokenHere
   ```

3. Save the file (Ctrl+O, Enter, Ctrl+X in nano)

### Step 3: Start the Services with Docker

```bash
# Build and start all services
docker-compose up -d

# Check if services are running
docker-compose ps
```

You should see two services running:
- `student-survey-app` on port 8501
- `llm-service` on port 8000

### Step 4: Access ChatFriend

1. Open your browser and go to [http://localhost:8501](http://localhost:8501)
2. Navigate to **5_🤖_ChatFriend** in the sidebar
3. You should see "✅ LLM Service Connected (Hugging Face)"
4. Start analyzing your qualitative data!

### Step 5: Verify Everything is Working

Check service logs if you encounter issues:

```bash
# View all logs
docker-compose logs

# View just the LLM service logs
docker-compose logs llm-service

# View just the app logs
docker-compose logs app
```

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

### "LLM Service is not available"

**Check if the service is running:**
```bash
docker-compose ps
# Both services should show "Up"
```

**Check LLM service logs:**
```bash
docker-compose logs llm-service
```

**Restart the services:**
```bash
docker-compose restart llm-service
```

### "HF_API_KEY not set on server"

This means your Hugging Face API key is missing or incorrect.

1. Check your `.env` file:
   ```bash
   cat .env
   ```

2. Make sure it contains:
   ```
   HF_API_KEY=hf_YourActualTokenHere
   ```

3. Restart the services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### 404 Errors in Logs

The healthcheck might show 404 errors for the root route - this is normal. The actual API endpoints (`/chat` and `/summarize`) work fine.

### API timeout errors
- The service has a 90-second timeout
- If requests are timing out, try reducing the amount of text being analyzed
- Check your internet connection (the service needs to reach Hugging Face)

### Connection refused errors
- Make sure both containers are on the same network (`survey-network`)
- Check that the LLM service is running: `docker-compose ps`
- Try rebuilding: `docker-compose up -d --build`

## 💡 Tips for Best Results

1. **Be Specific** - The more specific your queries, the better the results
2. **Use Filters** - Narrow down to relevant subsets (Treatment only, specific region, etc.)
3. **Iterate** - Try different phrasings if you don't get good results
4. **Combine Methods** - Use keyword frequency to identify themes, then AI for deeper analysis
5. **Export Everything** - Download reports for documentation and sharing

## ☁️ Cloud vs Local LLM Comparison

| Aspect | Cloud (Current) | Local (Ollama) |
|--------|----------------|----------------|
| Setup | Quick, API key only | Complex, download models |
| Cost | Pay per use | Free after setup |
| Performance | Fast, consistent | Depends on hardware |
| Privacy | Data sent to HF | 100% private |
| Updates | Automatic | Manual |
| Requirements | Internet + API key | 8GB+ RAM + storage |

## 🔐 Privacy & Data Security

**Data handling:**
- Teacher responses are sent to Hugging Face's API for analysis
- Only the text selected for analysis is sent (not your entire database)
- Hugging Face processes requests and doesn't store them permanently
- Your API key is kept secure in the `.env` file
- All services run in isolated Docker containers

## 🚀 Advanced Usage

### Changing the LLM Model

The service uses `openai/gpt-oss-20b:groq` by default. To change it:

1. Edit `llm_api.py`:
   ```python
   HF_MODEL = "meta-llama/Llama-3.2-3B-Instruct"  # or another model
   ```

2. Rebuild the service:
   ```bash
   docker-compose up -d --build llm-service
   ```

**Popular alternatives:**
- `meta-llama/Llama-3.2-3B-Instruct` - Fast, good quality
- `mistralai/Mistral-7B-Instruct-v0.3` - Excellent for analysis
- `google/gemma-2-9b-it` - Google's model

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

