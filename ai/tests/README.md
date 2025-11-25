# AI Services Testing Suite

Simple visual test script for testing all 5 AI models through the Caddy reverse proxy.

## Services Being Tested

1. **Ollama/GPT-OSS** (port 8004) - Text generation with **gpt-oss:20b** model
2. **Whisper** (port 8000) - ROCm GPU-accelerated audio transcription (Czech language)
3. **NLLB-200** (port 8002) - ROCm GPU-accelerated Czech to English translation (3.3B model)
4. **Tesseract OCR** (port 8003) - PDF/Image text extraction (Czech + English)
5. **Schema Matcher** (port 8005) - LLM-powered CSV data extraction from unstructured text

## Quick Start

```bash
# Run the test script
./test_models.sh
```

## Test Data

The script uses small test samples in `test_data/`:
- `audio_sample_30s.mp3` - 30-second audio clip for transcription
- `czech_text_sample.txt` - Czech text for translation testing
- `sample_page1.pdf` - Single PDF page for OCR testing
- `schema_extraction_sample.txt` - Czech text for structured data extraction

## Configuration

By default, the script tests via: `http://192.168.191.189:8085`

To change the base URL, edit the `BASE_URL` variable in `test_models.sh`:

```bash
BASE_URL="http://localhost:8085"
```

## Prerequisites

Before running the tests, ensure:

1. All AI services are running on their respective ports
2. Caddy is running with the Caddyfile configuration
3. The services are accessible from your machine

### Check Services Status

```bash
# Check if Caddy is running
systemctl status caddy

# Check individual services
curl http://192.168.191.189:8004/  # Ollama
curl http://192.168.191.189:8000/  # Whisper
curl http://192.168.191.189:8002/  # NLLB
curl http://192.168.191.189:8003/  # Tesseract
curl http://192.168.191.189:8005/health  # Schema Matcher
```

## Expected Output

The script provides visual feedback with:
- Colored headers for each test
- Success/failure status with HTTP codes
- Sample responses from each service
- Progress indicators

Example successful output:
```
╔════════════════════════════════════════════════════════════╗
║          AI Services Test Suite                           ║
║          Testing 5 Models via Caddy Proxy                 ║
╚════════════════════════════════════════════════════════════╝

[1/5] Testing Ollama/GPT-OSS (Text Generation)
✓ SUCCESS (HTTP 200)
Response: AI was first coined as a term in 1956...

[2/5] Testing Whisper (Audio Transcription)
✓ SUCCESS (HTTP 200)
Transcription: Kdyby to bylo nekomfortní...

[5/5] Testing Schema Matcher (CSV Data Extraction)
✓ SUCCESS (HTTP 200)
Relevance Score: 0.95
```

## Troubleshooting

**All tests fail with HTTP 000:**
- Services are not running or not accessible
- Check network connectivity to 192.168.191.189
- Try changing BASE_URL to `http://localhost:8085` if testing locally

**Specific service fails:**
- Check if that particular service is running
- Review Caddy logs: `journalctl -u caddy -f`
- Check service logs for the specific port

**Audio/PDF upload fails:**
- Ensure test data files exist in `test_data/`
- Check file permissions
- Verify curl supports file uploads (`curl --version`)
