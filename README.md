# **AI-Powered Educational Data Analysis Platform**
## **1. One-Sentence Description**
An AI-powered analytics platform that ingests diverse educational data, understands it using LLMs, and transforms it into actionable insights to improve learning outcomes and operational efficiency.
----------
## **2. Technology Stack**
### **Languages**
-   Node.js (backend & AI data processing)
-   Next.js (frontend, dashboards)
### **AI & Data Processing**
-   **Google Gemini Pro (Vertex AI, EU region)**
-   **Google Cloud Speech-to-Text (EU region)** - manualy, intended to be automated

### **Storage**
-   GoogleCloudBucket
-   MongoDB Atlas (EU region, free tier for development)

### **Intended Infrastructure**
-   Docker containers
-   Google Cloud Run or GKE
-   Artifact Registry (EU regions)
-   gcloud CLI
----------
## **3. Data Privacy Statement**
### **a. Where is data processed?**
-   Local servers (on-premise)
-   Google Cloud **EU regions only** (`europe-west4`, `europe-west1`)
### **b. Which AI services are used?**
-   **Gemini Pro** (Vertex AI EU region)
-   **Google Cloud Speech-to-Text (EU region)**
### **c. Does data leave the EU?**
**No.**
All services and infrastructures are configured to operate **exclusively within the EU**.
No audio, transcripts, or identifiable educational data is transferred outside EU data centers.
### **d. Monthly cost estimate**
Component
Estimated Cost
-   **Gemini Pro (Vertex AI EU)**	~€50 / month
-   **Network traffic**		~€20 / month
-   **Speech-to-Text**		~$0.014 per minute (≈ €13 / 1000 minutes)
-   **MongoDB Atlas (Free Tier)**		€0
-   Total typical cost: **€70–90/month + audio usage**.
----------
## **4. Prerequisites**
### **For Local Development**
-   Typesript
-   Node.js
-   Next.js
-   React
-   git
-   Docker & Docker Compose
-   ffmpeg
-   Google Cloud Project (EU)
-   gcloud CLI installed
-   MongoDB instance (Atlas EU region)
### **For Production**
-   Google Cloud project with billing
-   Artifact Registry (EU)
-   Cloud Run or GKE (EU)
-   Service Account with:
    -   Vertex AI User
    -   Cloud Speech Client
    -   Secret Manager Access
----------
## **5. Setup Instructions**
In the srcs/hackaton folder run:
-   pnpm install
-   pnpm build

## **6. How to run locally**
In the srcs/hackaton folder run:
-   pnpm start

## **7. How to deploy to production - intended**
-   CI/CD pipeline - GH actions
-   gcloud CLI with docker containers

## **8. Known limitations**




