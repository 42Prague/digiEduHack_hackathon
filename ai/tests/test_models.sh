#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Base URL - Caddy proxy
BASE_URL="http://localhost:8085"

# Print header
echo -e "${BOLD}${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║          AI Services Test Suite                           ║"
echo "║          Testing 5 Models via Caddy Proxy                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Test 1: Ollama/GPT-OSS
echo -e "\n${BOLD}${BLUE}[1/5] Testing Ollama/GPT-OSS (Text Generation)${NC}"
ENDPOINT="${BASE_URL}/ollama/api/generate"
echo -e "${YELLOW}Endpoint: ${ENDPOINT}${NC}"
echo -e "${CYAN}Model: gpt-oss:20b${NC}"
echo -e "${CYAN}Sending: 'Tell me a fun fact about AI in one sentence'${NC}"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:20b",
    "prompt": "Tell me a fun fact about AI in one sentence",
    "stream": false
  }' 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ SUCCESS${NC} (HTTP $HTTP_CODE)"
    echo -e "${CYAN}Response:${NC}"
    echo "$BODY" | grep -o '"response":"[^"]*"' | sed 's/"response":"//;s/"$//' | fold -w 60 -s
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $HTTP_CODE)"
    echo "$BODY" | head -3
fi

# Test 2: Whisper Transcription
echo -e "\n${BOLD}${BLUE}[2/5] Testing Whisper (Audio Transcription)${NC}"
ENDPOINT="${BASE_URL}/transcription/transcribe"
echo -e "${YELLOW}Endpoint: ${ENDPOINT}${NC}"
echo -e "${CYAN}Uploading: test_data/audio_sample_30s.mp3 (30 seconds)${NC}"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${ENDPOINT}" \
  -F "file=@test_data/audio_sample_30s.mp3" \
  -F "language=cs" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ SUCCESS${NC} (HTTP $HTTP_CODE)"
    echo -e "${CYAN}Transcription:${NC}"
    echo "$BODY" | grep -o '"text":"[^"]*"' | sed 's/"text":"//;s/"$//' | fold -w 60 -s
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $HTTP_CODE)"
    echo "$BODY" | head -3
fi

# Test 3: NLLB Translation
echo -e "\n${BOLD}${BLUE}[3/5] Testing NLLB-200 (Czech to English Translation)${NC}"
ENDPOINT="${BASE_URL}/translation/translate"
echo -e "${YELLOW}Endpoint: ${ENDPOINT}${NC}"
echo -e "${CYAN}Translating Czech text to English${NC}"
echo ""

CZECH_TEXT=$(cat test_data/czech_text_sample.txt | tr '\n' ' ')
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$CZECH_TEXT\", \"source_lang\": \"cs\", \"target_lang\": \"en\"}" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ SUCCESS${NC} (HTTP $HTTP_CODE)"
    echo -e "${CYAN}Original (Czech):${NC}"
    echo "$CZECH_TEXT" | fold -w 60 -s
    echo ""
    echo -e "${CYAN}Translation (English):${NC}"
    echo "$BODY" | grep -o '"text":"[^"]*"' | sed 's/"text":"//;s/"$//' | fold -w 60 -s
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $HTTP_CODE)"
    echo "$BODY" | head -3
fi

# Test 4: Tesseract OCR
echo -e "\n${BOLD}${BLUE}[4/5] Testing Tesseract (OCR - PDF to Text)${NC}"
ENDPOINT="${BASE_URL}/ocr/ocr"
echo -e "${YELLOW}Endpoint: ${ENDPOINT}${NC}"
echo -e "${CYAN}Uploading: test_data/sample_page1.pdf (page 1)${NC}"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${ENDPOINT}" \
  -F "file=@test_data/sample_page1.pdf" \
  -F "lang=ces+eng" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ SUCCESS${NC} (HTTP $HTTP_CODE)"
    echo -e "${CYAN}Extracted Text (first 200 chars):${NC}"
    echo "$BODY" | grep -o '"text":"[^"]*"' | sed 's/"text":"//;s/"$//' | head -c 200 | fold -w 60 -s
    echo "..."
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $HTTP_CODE)"
    echo "$BODY" | head -3
fi

# Test 5: Schema Matcher (CSV Data Extraction)
echo -e "\n${BOLD}${BLUE}[5/5] Testing Schema Matcher (CSV Data Extraction)${NC}"
ENDPOINT="${BASE_URL}/schema/extract"
echo -e "${YELLOW}Endpoint: ${ENDPOINT}${NC}"
echo -e "${CYAN}Extracting structured data from Czech text${NC}"
echo ""

EXTRACTION_TEXT=$(cat test_data/schema_extraction_sample.txt | tr '\n' ' ')
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"$EXTRACTION_TEXT\",
    \"schema\": [
      {\"name\": \"role\", \"type\": \"string\", \"description\": \"Job role or position\"},
      {\"name\": \"age\", \"type\": \"number\", \"description\": \"Age in years\"},
      {\"name\": \"experience\", \"type\": \"number\", \"description\": \"Years of experience\"}
    ]
  }" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ SUCCESS${NC} (HTTP $HTTP_CODE)"
    echo -e "${CYAN}Relevance Score:${NC}"
    echo "$BODY" | grep -o '"relevance_score":[0-9.]*' | sed 's/"relevance_score"://'
    echo ""
    echo -e "${CYAN}Extracted Rows:${NC}"
    echo "$BODY" | grep -o '"rows":\[[^]]*\]' | head -c 200
    echo "..."
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $HTTP_CODE)"
    echo "$BODY" | head -3
fi

# Summary
echo -e "\n${BOLD}${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Test Complete                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
