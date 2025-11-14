# 🚀 Setup Guide: Student Performance Survey System

Complete setup instructions for deploying the web-based survey and analytics platform.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Database Configuration](#database-configuration)
4. [Running the Application](#running-the-application)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Software Requirements
- **Python**: 3.8 or higher
- **Database** (choose one):
  - SQLite (included with Python, good for testing)
  - PostgreSQL 12+ (recommended for production)
  - MySQL 8.0+
- **Web Browser**: Modern browser (Chrome, Firefox, Safari, Edge)

### Hardware Requirements
- **Minimum**: 2GB RAM, 10GB disk space
- **Recommended**: 4GB+ RAM, 20GB+ disk space

---

## 📦 Installation

### Step 1: Clone or Download the Project

```bash
# If using git
git clone <your-repository-url>
cd afolder

# Or download and extract the ZIP file
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

**Key packages installed:**
- `streamlit` - Web application framework
- `pandas`, `numpy` - Data processing
- `plotly` - Interactive visualizations
- `sqlalchemy` - Database connectivity
- `psycopg2-binary` - PostgreSQL driver
- `pymysql` - MySQL driver

---

## 🗄️ Database Configuration

### Option A: SQLite (Quick Start - Recommended for Testing)

**Easiest option - no external database needed!**

1. Update `.streamlit/secrets.toml`:

```toml
[sqlite]
db_path = "teacher_survey.db"
```

2. The database file will be created automatically when you first run the app.

**Pros:**
- No installation needed
- Perfect for development and testing
- Portable (single file database)

**Cons:**
- Not suitable for high concurrency
- Limited to single server

---

### Option B: PostgreSQL (Recommended for Production)

#### 1. Install PostgreSQL

**On Mac (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**On Windows:**
Download from: https://www.postgresql.org/download/windows/

#### 2. Create Database

```bash
# Connect to PostgreSQL
psql postgres

# In PostgreSQL prompt:
CREATE DATABASE teacher_survey_db;
CREATE USER survey_admin WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE teacher_survey_db TO survey_admin;
\q
```

#### 3. Create Tables

```bash
# Run the schema script
psql -U survey_admin -d teacher_survey_db -f database_setup.sql
```

#### 4. Configure Streamlit Secrets

Edit `.streamlit/secrets.toml`:

```toml
db_type = "postgresql"
db_host = "localhost"
db_port = "5432"
db_name = "teacher_survey_db"
db_user = "survey_admin"
db_password = "your_secure_password"
```

---

### Option C: MySQL

#### 1. Install MySQL

**On Mac (using Homebrew):**
```bash
brew install mysql
brew services start mysql
```

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
```

**On Windows:**
Download from: https://dev.mysql.com/downloads/

#### 2. Create Database

```bash
# Connect to MySQL
mysql -u root -p

# In MySQL prompt:
CREATE DATABASE teacher_survey_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'survey_admin'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON teacher_survey_db.* TO 'survey_admin'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 3. Create Tables

```bash
mysql -u survey_admin -p teacher_survey_db < database_setup.sql
```

#### 4. Configure Streamlit Secrets

Edit `.streamlit/secrets.toml`:

```toml
db_type = "mysql"
db_host = "localhost"
db_port = "3306"
db_name = "teacher_survey_db"
db_user = "survey_admin"
db_password = "your_secure_password"
```

---

## 🚀 Running the Application

### Local Development

1. **Activate virtual environment** (if not already activated):

```bash
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

2. **Run the Streamlit app**:

```bash
streamlit run app.py
```

3. **Access the application**:

The app will automatically open in your browser at:
```
http://localhost:8501
```

If it doesn't open automatically, navigate to that URL in your browser.

### Custom Port or Host

```bash
# Run on custom port
streamlit run app.py --server.port 8080

# Run on specific address
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

---

## 🧪 Testing

### 1. Test Database Connection

Create a test file `test_db.py`:

```python
from database_utils import get_database_connection, get_all_responses

engine = get_database_connection()
print("✓ Database connection successful!")

responses = get_all_responses(engine, limit=5)
print(f"✓ Found {len(responses) if responses is not None else 0} responses")
```

Run it:
```bash
python test_db.py
```

### 2. Test the Survey Form

1. Navigate to **Survey Form** page
2. Fill in all required fields
3. Submit the form
4. Check that success message appears

### 3. Test Natural Language Queries

1. Navigate to **Ask Questions** page
2. Try these queries:
   - "What is the average performance by region?"
   - "Show me performance trends over time"
   - "Which schools are performing best?"

### 4. Test the Dashboard

1. Navigate to **Dashboard** page
2. Check that all visualizations load
3. Try different filters
4. Verify data updates correctly

---

## 🌐 Deployment

### Option 1: Streamlit Cloud (Easiest)

**Free hosting for Streamlit apps!**

1. **Push code to GitHub**:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

2. **Deploy on Streamlit Cloud**:

- Go to https://streamlit.io/cloud
- Sign in with GitHub
- Click "New app"
- Select your repository
- Main file: `app.py`
- Click "Deploy"

3. **Add Secrets**:

In Streamlit Cloud dashboard:
- Go to your app settings
- Add secrets from `.streamlit/secrets.toml`

4. **Database Considerations**:

For Streamlit Cloud, use one of these:
- SQLite (included in deployment)
- External PostgreSQL (recommended):
  - Use [ElephantSQL](https://www.elephantsql.com/) (free tier available)
  - Use [Supabase](https://supabase.com/) (free tier available)
  - Use [Heroku Postgres](https://www.heroku.com/postgres)

---

### Option 2: Docker Deployment

1. **Create `Dockerfile`**:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

2. **Build and run**:

```bash
# Build image
docker build -t survey-app .

# Run container
docker run -p 8501:8501 survey-app
```

---

### Option 3: Traditional Server

**For Ubuntu/Debian server:**

1. **Install dependencies**:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx
```

2. **Set up application**:

```bash
cd /var/www/survey-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Create systemd service** (`/etc/systemd/system/survey-app.service`):

```ini
[Unit]
Description=Student Performance Survey App
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/survey-app
Environment="PATH=/var/www/survey-app/venv/bin"
ExecStart=/var/www/survey-app/venv/bin/streamlit run app.py --server.port 8501

[Install]
WantedBy=multi-user.target
```

4. **Start service**:

```bash
sudo systemctl start survey-app
sudo systemctl enable survey-app
```

5. **Configure Nginx** (optional, for SSL/domain):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'streamlit'"

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Database connection failed"

**Solution:**
1. Check that database service is running:
   ```bash
   # PostgreSQL
   sudo systemctl status postgresql
   
   # MySQL
   sudo systemctl status mysql
   ```

2. Verify credentials in `.streamlit/secrets.toml`
3. Test connection manually:
   ```bash
   # PostgreSQL
   psql -U survey_admin -d teacher_survey_db
   
   # MySQL
   mysql -u survey_admin -p teacher_survey_db
   ```

### Issue: "Port 8501 already in use"

**Solution:**
```bash
# Find process using port 8501
lsof -i :8501

# Kill the process
kill -9 <PID>

# Or use different port
streamlit run app.py --server.port 8502
```

### Issue: "Permission denied" when creating database file

**Solution:**
```bash
# Make sure current user owns the directory
sudo chown -R $USER:$USER .

# Or specify full path with write permissions
```

### Issue: Visualizations not showing

**Solution:**
1. Clear browser cache
2. Check browser console for errors (F12)
3. Verify data exists:
   ```bash
   python -c "from database_utils import *; print(get_all_responses(get_database_connection()))"
   ```

---

## 📊 Initial Data Setup

### Option 1: Manual Entry via Form

1. Run the application
2. Navigate to Survey Form
3. Submit responses manually

### Option 2: Import Sample Data

Create `import_sample_data.py`:

```python
from database_utils import get_database_connection
import pandas as pd

engine = get_database_connection()

# Load your CSV
df = pd.read_csv('data_structure_template.csv')

# Import to database
df.to_sql('teacher_survey_responses', engine, if_exists='append', index=False)

print(f"Imported {len(df)} responses!")
```

Run it:
```bash
python import_sample_data.py
```

---

## 🔐 Security Best Practices

### 1. Protect Secrets File

```bash
# Never commit secrets to git
echo ".streamlit/secrets.toml" >> .gitignore
```

### 2. Use Strong Passwords

- Database passwords: 16+ characters, mixed case, numbers, symbols
- Change default passwords immediately

### 3. Database Security

```sql
-- PostgreSQL: Restrict connections
# Edit /etc/postgresql/*/main/pg_hba.conf
host    teacher_survey_db    survey_admin    127.0.0.1/32    md5

-- Create read-only user for dashboard
CREATE USER dashboard_viewer WITH PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dashboard_viewer;
```

### 4. HTTPS in Production

- Use SSL certificate (Let's Encrypt)
- Configure Nginx with HTTPS
- Redirect HTTP to HTTPS

---

## 📚 Additional Resources

### Documentation
- [Streamlit Docs](https://docs.streamlit.io/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Plotly Docs](https://plotly.com/python/)

### Support
- Check `README_PROJECT_OVERVIEW.md` for project details
- Review `mixed_effects_model_analysis_guide.md` for analysis help
- Consult `codebook.md` for data dictionary

---

## ✅ Deployment Checklist

Before going live:

- [ ] Database configured and tested
- [ ] All dependencies installed
- [ ] Secrets file configured (and not in git!)
- [ ] Test all three pages (Form, Questions, Dashboard)
- [ ] Submit test survey response
- [ ] Verify queries work
- [ ] Check visualizations render correctly
- [ ] Set up backups for database
- [ ] Configure monitoring (optional)
- [ ] Document any custom configuration
- [ ] Train users on system

---

## 🎉 You're Ready!

Your Student Performance Survey System is now set up and ready to use!

**Next Steps:**
1. Share the URL with teachers to start collecting data
2. Monitor responses in the Dashboard
3. Use natural language queries for custom analysis
4. Export data for statistical analysis (see mixed effects guide)

**Need Help?**
- Check the troubleshooting section above
- Review error logs in terminal
- Consult Streamlit documentation

---

*Last updated: 2025-11*
*Version: 1.0*






