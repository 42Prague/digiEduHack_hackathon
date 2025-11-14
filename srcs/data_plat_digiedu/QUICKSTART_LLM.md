# 🚀 Quick Start: ChatFriend with Hugging Face LLM

## What Changed?

ChatFriend now uses **Hugging Face's cloud-based LLM API** instead of running Ollama locally. This means:
- ✅ Easier setup (just need an API key)
- ✅ No need to download large model files
- ✅ Faster and more consistent performance
- ✅ Works on any hardware
- ⚠️ Requires internet connection
- ⚠️ Small cost per API call (Hugging Face has free tier)

## 3-Step Setup

### 1️⃣ Get Your API Key

1. Visit [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Give it a name (e.g., "ChatFriend")
4. Select "Read" role
5. Click "Generate token"
6. **Copy the token** (starts with `hf_...`)

### 2️⃣ Add the API Key

Open the `.env` file in the `data_plat_digiedu` directory:

```bash
cd /Users/kira/fuckk/srcs/data_plat_digiedu
nano .env
```

Replace `your_huggingface_api_key_here` with your actual token:

```
HF_API_KEY=hf_YourActualTokenHere
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

### 3️⃣ Start the Services

```bash
# Stop any running containers
docker-compose down

# Rebuild and start with the new configuration
docker-compose up -d --build

# Check that both services are running
docker-compose ps
```

You should see:
- ✅ `student-survey-app` - Running on port 8501
- ✅ `llm-service` - Running on port 8000

## ✅ Verify It Works

1. Open your browser: [http://localhost:8501](http://localhost:8501)
2. Click on **5_🤖_ChatFriend** in the sidebar
3. Look for the status message at the top

**Success looks like:**
```
✅ LLM Service Connected (Hugging Face)
🌐 Service URL: http://llm-service:8000
```

**If you see an error:**
- Check your API key is correct in `.env`
- Make sure both services are running: `docker-compose ps`
- View logs: `docker-compose logs llm-service`

## 🎯 Try It Out

1. Go to the **Theme Extraction** tab
2. Select "AI Analysis (LLM)"
3. Click "🎯 Extract Themes"
4. Wait 10-30 seconds for the AI analysis

If it works, you'll see a detailed analysis of themes in your teacher responses!

## 🔧 Common Issues

### "HF_API_KEY not set on server"
- Your `.env` file is missing or the key is wrong
- Edit `.env` and add your key
- Restart: `docker-compose restart llm-service`

### "Cannot connect to LLM service"
- The LLM service isn't running
- Check: `docker-compose ps`
- Restart: `docker-compose up -d llm-service`

### Timeout errors
- Your internet connection might be slow
- The HF API might be busy
- Try again in a few seconds

## 💰 Cost Information

Hugging Face offers:
- **Free tier**: Limited requests per month (usually sufficient for testing)
- **Pro tier**: $9/month for more requests
- **Pay-as-you-go**: Small cost per token

For typical ChatFriend usage (analyzing 20-30 responses at a time), you'll likely stay within the free tier during development.

## 📚 Next Steps

- Read the full [CHATFRIEND_SETUP.md](CHATFRIEND_SETUP.md) for advanced features
- Try different analysis types (Comparative, Temporal, Summary)
- Export your reports for documentation

## 🆘 Need Help?

Check the logs:
```bash
# All logs
docker-compose logs

# Just LLM service
docker-compose logs llm-service

# Follow logs in real-time
docker-compose logs -f
```

---

**🎉 Congratulations!** You've successfully integrated the Hugging Face LLM into your data platform!

