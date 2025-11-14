# EduScale Engine

**DigiEduHack 2025 Submission** - Open-source data infrastructure for scaling educational impact across 5,000+ Czech schools.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.10+ (for local backend development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd digiEduHack_hackathon
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set your FEATHERLESS_API_KEY
   ```

3. **Start the application**
   ```bash
   docker compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📋 Features

### Data Ingestion
- **Multi-format support**: CSV, Excel, JSON, TXT, Markdown, DOCX
- **Audio/Transcript upload**: Support for audio files and transcript text
- **Metadata validation**: Enforced validation of all required fields
- **Automatic data quality scoring**: DQ reports generated automatically

### Cultural Analysis
- **AI-powered analysis**: Uses Featherless.ai (Meta-Llama 3.1) for cultural insights
- **Comprehensive scoring**: Mindset shift, collaboration, teacher confidence, municipality cooperation, sentiment
- **Theme extraction**: Automatic identification of key themes
- **Impact summaries**: AI-generated summaries of practical and mindset changes

### Analytics & Insights
- **School comparison**: Compare schools across multiple dimensions
- **Region insights**: Aggregate analysis by region
- **Trend analysis**: Time-series analysis of cultural metrics
- **Recommendations**: AI-powered actionable recommendations

### Data Quality
- **Automatic DQ scoring**: Schema validation, missing values, PII detection
- **Quarantine system**: Isolate problematic data
- **Normalization**: Automatic data cleaning and standardization

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: React + TypeScript + Vite
- **Database**: PostgreSQL 15
- **AI**: Featherless.ai (Meta-Llama 3.1-8B-Instruct)

## 📁 Project Structure

```
digiEduHack_hackathon/
├── src/
│   ├── backend/          # FastAPI backend
│   │   ├── swx_api/      # Main application code
│   │   ├── migrations/   # Database migrations
│   │   └── Dockerfile
│   └── frontend/         # React frontend
│       ├── src/
│       └── Dockerfile
├── docker-compose.yml    # Docker orchestration
├── requirements.txt      # Python dependencies
└── .env.example         # Environment variables template
```

## 🔧 Configuration

### Required Environment Variables

- `FEATHERLESS_API_KEY`: API key for Featherless.ai (required for AI features)
- `DB_HOST`: Database host (default: `db` in Docker, `localhost` locally)
- `DB_USER`: Database username (default: `swx_user`)
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name (default: `swx_db`)

See `.env.example` for all available configuration options.

## 📊 API Endpoints

### Ingestion
- `POST /api/ingestion/ingest` - Upload data files
- `POST /api/ingestion/upload_audio` - Upload audio/transcript with metadata
- `GET /api/ingestion/datasets` - List all datasets
- `GET /api/ingestion/dq_report/{dataset_id}` - Get data quality report

### Transcripts
- `GET /api/transcripts` - List transcripts (with filters)
- `GET /api/transcripts/{id}` - Get transcript details

### Analytics
- `GET /api/analytics/summary` - Get analytics summary
- `GET /api/analytics/region_insights?region_id={id}` - Get region insights
- `GET /api/analytics/recommendations?school_id={id}` - Get recommendations
- `GET /api/analytics/trends?metric={name}` - Get metric trends

### Schools
- `GET /api/schools/compare?school_id_1={id}&school_id_2={id}&metric={name}` - Compare schools
- `GET /api/schools/compare_by_dimension?dimension={type}` - Compare by dimension

## 🧪 Testing

### Backend Tests
```bash
cd src/backend
pytest tests/
```

### Frontend Tests
```bash
cd src/frontend
npm test
```

## 📝 License

MIT LICENSE

## 👥 Team

- Aliyu Abdulbasit Ayinde -  Lead AI Engineer & System Architect
- Štěpán Kapko -  Frontend / UI
- Husam Ahmad - AI Engineer & Marketing 
- Sridharan Kaliyamoorthy - Data Analysis, Audio Data Ingestion & Validation


## 🙏 Acknowledgments

- Eduzměna Foundation
- DigiEduHack 2025 organizers
- Featherless.ai for AI infrastructure


## 🎯 Demo Data

This package includes **pre-generated demo data** for immediate demonstration:

### Quick Load Demo Data

```bash
# 1. Start services
docker compose up -d

# 2. Run migrations (creates tables)
docker compose exec backend alembic upgrade head

# 3. Load demo data
docker compose exec -T db psql -U swx_user -d swx_db < mock_data/insert_transcripts.sql
docker compose exec -T db psql -U swx_user -d swx_db < mock_data/insert_cultural_analysis.sql

# 4. Verify
docker compose exec db psql -U swx_user -d swx_db -c "SELECT COUNT(*) FROM transcripts;"
```

### Demo Data Includes

- **15 Transcripts** from 7 regions, 4 school types, 5 intervention types
- **15 Cultural Analyses** with complete scoring
- **5 DQ Reports** showing various quality scenarios
- **API Response Examples** for testing

See `DEMO_DATA_INSTRUCTIONS.md` for detailed demo setup and screenshot opportunities.
