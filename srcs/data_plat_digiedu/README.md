# 📚 Student Performance Survey System

A comprehensive web-based platform for collecting, analyzing, and visualizing teacher perceptions of student performance across schools and regions.

![Version](https://img.shields.io/badge/version-1.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## 🎯 Project Overview

This system provides a complete solution for educational research focused on measuring student performance through teacher assessments, with particular emphasis on:

- **Regional comparisons** across different geographic areas
- **Intervention effectiveness** tracking over time
- **School-level performance** monitoring
- **Mixed effects statistical analysis** capabilities

### Key Features

✅ **Web-based Survey Form** - Easy data collection interface for teachers  
✅ **Database Storage** - Secure PostgreSQL/MySQL/SQLite backend  
✅ **Natural Language Queries** - Ask questions in plain English  
✅ **Interactive Dashboard** - Real-time analytics and visualizations  
✅ **Statistical Analysis** - Built-in mixed effects modeling (R/Python)  
✅ **Export Capabilities** - Download data and reports

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Database (SQLite/PostgreSQL/MySQL)
- Modern web browser

### Installation (5 minutes)

```bash
# 1. Clone or download the project
cd /path/to/afolder

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`

**That's it!** By default, it uses SQLite (no external database needed).

---

## 📁 Project Structure

```
afolder/
│
├── app.py                              # Main application entry point
├── database_utils.py                   # Database connection & operations
├── requirements.txt                    # Python dependencies
│
├── pages/                              # Multi-page app structure
│   ├── 1_📝_Survey_Form.py            # Teacher questionnaire
│   ├── 2_🔍_Ask_Questions.py          # Natural language query interface
│   └── 3_📊_Dashboard.py              # Analytics dashboard
│
├── .streamlit/
│   └── secrets.toml                    # Database credentials (DON'T COMMIT!)
│
├── database_setup.sql                  # SQL schema for database creation
├── data_structure_template.csv         # Example data structure
│
├── teacher_questionnaire_revised.md    # Questionnaire documentation
├── codebook.md                         # Data dictionary
│
├── mixed_effects_analysis.R            # Statistical analysis (R)
├── mixed_effects_analysis.py           # Statistical analysis (Python)
├── mixed_effects_model_analysis_guide.md # Analysis guide
│
├── SETUP_GUIDE.md                      # Detailed setup instructions
├── README_PROJECT_OVERVIEW.md          # Complete project documentation
└── README.md                           # This file
```

---

## 🖥️ Application Pages

### 1️⃣ Survey Form Page

**For Teachers:**
- Complete the validated questionnaire
- Assess student performance across 8 dimensions
- Submit responses directly to database
- Automatic duplicate detection

**Features:**
- Conditional logic (intervention-specific questions)
- Input validation
- Real-time feedback
- Mobile-responsive design

### 2️⃣ Ask Questions Page

**For Researchers & Administrators:**
- Ask questions in plain English
- Automatic SQL query generation
- Interactive visualizations
- Export results to CSV

**Example Queries:**
- *"What is the average performance by region?"*
- *"Show me performance trends over time"*
- *"Which schools are performing best?"*
- *"Compare intervention and control groups"*

### 3️⃣ Dashboard Page

**For Everyone:**
- Real-time analytics and KPIs
- Regional performance comparisons
- School-level analysis
- Temporal trends
- Interactive filtering
- Export-ready visualizations

---

## 📊 Data Analysis Capabilities

### Built-in Dashboard Analytics

- **Descriptive Statistics**: Means, standard deviations, counts
- **Comparative Analysis**: Regional/school/intervention comparisons
- **Temporal Trends**: Performance over time
- **Visualizations**: Bar charts, line graphs, radar charts, heatmaps

### Advanced Statistical Analysis

The project includes complete R and Python scripts for:

**Mixed Effects Models** (Hierarchical Linear Models)
- Account for nested data structure (students → teachers → schools → regions)
- Test intervention effects over time
- Partition variance by level
- Calculate ICC, marginal/conditional R²

**Key Research Questions:**
1. Do intervention schools perform better?
2. Does performance improve over time?
3. Does intervention effect increase over time?
4. Do effects vary by region?

See `mixed_effects_model_analysis_guide.md` for complete analysis guide.

---

## 🗄️ Database Configuration

### SQLite (Default - Easiest)

No configuration needed! Database file created automatically.

### PostgreSQL (Recommended for Production)

```toml
# .streamlit/secrets.toml
db_type = "postgresql"
db_host = "localhost"
db_port = "5432"
db_name = "teacher_survey_db"
db_user = "survey_admin"
db_password = "your_password"
```

### MySQL

```toml
# .streamlit/secrets.toml
db_type = "mysql"
db_host = "localhost"
db_port = "3306"
db_name = "teacher_survey_db"
db_user = "survey_admin"
db_password = "your_password"
```

**See `SETUP_GUIDE.md` for detailed database setup instructions.**

---

## 📝 Questionnaire Design

The survey captures:

**Section A: Demographics & Context**
- School, region, teacher info
- Intervention status and duration

**Section B: Current Performance (8 Dimensions)**
- Overall academic performance
- Problem-solving skills
- Critical thinking
- Collaboration
- Communication
- Engagement
- Behavior/attitude
- Persistence/resilience

**Section C: Changes Over Time**
- Performance trajectory
- Improvement indicators

**Section D: Intervention Effectiveness** (Treatment group only)
- Overall impact rating
- Skills most improved
- Effective components

**Section E: Teaching Practices**
- Important learning elements
- Practice changes

**Section F: Qualitative Insights**
- Open-ended responses
- Challenges and successes

---

## 📈 Use Cases

### For Teachers
✓ Submit performance assessments  
✓ Track student progress over time  
✓ Reflect on teaching practices

### For School Administrators
✓ Monitor school performance  
✓ Compare with regional averages  
✓ Identify areas for improvement  
✓ Track intervention implementation

### For Researchers
✓ Collect systematic data  
✓ Run statistical analyses  
✓ Test research hypotheses  
✓ Publish findings

### For District/Regional Coordinators
✓ Compare schools and regions  
✓ Evaluate intervention programs  
✓ Make data-driven decisions  
✓ Allocate resources effectively

---

## 🛠️ Technical Stack

**Frontend:**
- Streamlit (Python web framework)
- Plotly (interactive visualizations)
- HTML/CSS (custom styling)

**Backend:**
- SQLAlchemy (database ORM)
- Pandas (data processing)
- NumPy (numerical operations)

**Database:**
- PostgreSQL / MySQL / SQLite

**Analysis:**
- R (lme4, lmerTest for mixed effects)
- Python (statsmodels for mixed effects)
- Plotly/ggplot2 (visualizations)

---

## 📚 Documentation

- **`SETUP_GUIDE.md`** - Complete installation and deployment guide
- **`README_PROJECT_OVERVIEW.md`** - Comprehensive project documentation
- **`mixed_effects_model_analysis_guide.md`** - Statistical analysis tutorial
- **`codebook.md`** - Data dictionary and variable definitions
- **`teacher_questionnaire_revised.md`** - Full questionnaire with rationale

---

## 🚀 Deployment Options

### 1. Local Development
```bash
streamlit run app.py
```

### 2. Streamlit Cloud (Free!)
- Push to GitHub
- Deploy at https://streamlit.io/cloud
- Add secrets in dashboard

### 3. Docker
```bash
docker build -t survey-app .
docker run -p 8501:8501 survey-app
```

### 4. Traditional Server
- Use systemd service
- Configure Nginx reverse proxy
- Set up SSL with Let's Encrypt

**See `SETUP_GUIDE.md` for detailed deployment instructions.**

---

## 🔐 Security

**Important Security Considerations:**

✅ **Never commit** `.streamlit/secrets.toml` to version control  
✅ Use **strong passwords** for database accounts  
✅ Enable **SSL/HTTPS** in production  
✅ Create **read-only database users** for dashboards  
✅ Implement **input validation** (already included)  
✅ Regular **database backups**  
✅ Monitor **access logs**

---

## 🧪 Testing

### Test Database Connection
```python
python test_db.py
```

### Test Survey Submission
1. Navigate to Survey Form
2. Fill required fields
3. Submit
4. Verify success message

### Test Natural Language Queries
1. Go to Ask Questions page
2. Try: "What is the average performance by region?"
3. Verify results display

### Test Dashboard
1. Navigate to Dashboard
2. Check all tabs load
3. Try filters
4. Verify visualizations render

---

## 📊 Sample Data

The project includes a sample dataset (`data_structure_template.csv`) with 10 example responses.

**To load sample data:**

```python
from database_utils import get_database_connection
import pandas as pd

engine = get_database_connection()
df = pd.read_csv('data_structure_template.csv')
df.to_sql('teacher_survey_responses', engine, if_exists='append', index=False)
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Visualizations powered by [Plotly](https://plotly.com/)
- Statistical analysis based on [lme4](https://github.com/lme4/lme4) methodology

---

## 📞 Support

**Having issues?**

1. Check `SETUP_GUIDE.md` troubleshooting section
2. Review error messages in terminal
3. Verify database connection
4. Check Streamlit documentation

**Need help with analysis?**

- Consult `mixed_effects_model_analysis_guide.md`
- Review sample R/Python analysis scripts
- Check statistical assumptions

**Contact:**
- Email: support@example.com
- Documentation: See project docs folder

---

## 🎯 Roadmap

**Future Enhancements:**

- [ ] User authentication system
- [ ] Email notifications for surveys
- [ ] Advanced NLP for query understanding
- [ ] Machine learning predictions
- [ ] Mobile app version
- [ ] Automated report generation
- [ ] Multi-language support
- [ ] Real-time collaboration features

---

## ⭐ Quick Links

- [Setup Guide](SETUP_GUIDE.md) - Installation instructions
- [Project Overview](README_PROJECT_OVERVIEW.md) - Complete documentation
- [Analysis Guide](mixed_effects_model_analysis_guide.md) - Statistical methods
- [Codebook](codebook.md) - Data dictionary

---

<div align="center">

### 🌟 Ready to Get Started?

```bash
pip install -r requirements.txt
streamlit run app.py
```

**Your survey system will be running at http://localhost:8501**

---

Made with ❤️ for educational research

</div>






