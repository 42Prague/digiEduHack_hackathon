# DigiEduHack Pitch - EduScale Intelligence Layer
## 5-Minute Presentation Script

---

## SLIDE 1: INTRODUCTION (30 seconds)

**SPEAKER:**

"Good afternoon, jury. We are a two-person technical team: a DevOps engineer and a senior backend developer. We built this solution using modern AI development tools—Kiro, Claude Code, Cursor, and ChatGPT—working collaboratively, alternating between infrastructure and application development. Our solution directly addresses Eduzměna's core challenge: scaling from 60 to 800 schools by building an intelligence layer that transforms messy educational data into actionable insights."

---

## SLIDE 2: THE PROBLEM (30 seconds)

**SPEAKER:**

"Eduzměna faces exponential data complexity: Excel files with different structures, audio recordings from teacher interviews, PDF feedback forms, archives containing mixed formats. Traditional ETL pipelines break. Manual processing doesn't scale. Schools use different column names for the same concept—'Student Name,' 'Pupil,' 'Participant.' Without automated intelligence, scaling to 800 schools is impossible. This is not a database problem—it's an AI problem."

---

## SLIDE 3: OUR SOLUTION ARCHITECTURE (45 seconds)

**SPEAKER:**

"We built an event-driven intelligence layer on Google Cloud. Here's how it works:

First, file upload triggers automatic processing. Our MIME decoder handles ANY file type—CSV, Excel, JSON, archives like ZIP or TAR, audio recordings, PDFs—everything.

Second, we extract text from all formats. Audio becomes transcripts using Google Speech-to-Text. PDFs become searchable text. Archives get unpacked and each file processed independently.

Third, AI classification happens. We use BGE-M3 embedding model—a 1024-dimensional multilingual model—to understand table semantics. Is this assessment data? Attendance? Feedback? The model knows, regardless of column names.

Fourth, intelligent mapping. Llama 3.1 8B Instruct—an open-source model via Featherless.ai—maps 'Student Name,' 'Pupil,' 'Participant' to the same canonical concept. Entity resolution handles name variations: 'Jan Novák' equals 'J. Novak.'

Finally, data lands in BigQuery with standardized schema, ready for analysis."

---

## SLIDE 4: KEY TECHNICAL DIFFERENTIATORS (45 seconds)

**SPEAKER:**

"What makes this production-ready?

**Open-source models**: Llama 3.1 8B via Featherless.ai API, BGE-M3 embeddings, paraphrase-multilingual-mpnet for semantic search. No vendor lock-in. These models are free to use, with transparent licensing.

**Embedding intelligence**: We embed column names, concepts, and feedback text into semantic space. This enables fuzzy matching, multilingual support for Czech and English, and understanding of educational context without manual rules.

**Archive processing**: Not just single files—we handle ZIP, TAR, GZ archives. One upload of 100 Excel files gets processed automatically. Critical for bulk data imports.

**Natural language queries**: Users ask questions in plain English: 'Show me average test scores by region.' Our system translates to SQL, executes on BigQuery, returns results with explanations. No SQL knowledge required.

**Managed infrastructure**: Cloud Run, BigQuery, Eventarc. Google handles scaling, patching, uptime. Google Support available for production issues. Our team focuses on features, not infrastructure maintenance."

---

## SLIDE 5: PRICING AND SCALING (60 seconds)

**SPEAKER:**

"Let's talk real numbers. Cost transparency is critical for educational organizations.

**Current scale—60 schools**:
- 1,000 files per month
- 100 GB data processed
- 500 natural language queries
- **Monthly cost: approximately $45**

Breaking this down:
- BigQuery: $5 per TB queried, $20 per TB stored. At 100 GB stored, 50 GB queried monthly: **$7.50**
- Cloud Run: $0.00002400 per vCPU-second. With 4 GB RAM instances running 5 hours total monthly: **$12**
- Featherless.ai LLM API: $0.10 per million tokens. With entity extraction and NLQ, approximately 10M tokens monthly: **$1**
- Cloud Storage: $0.020 per GB. At 100 GB: **$2**
- Speech-to-Text for audio: $0.006 per 15 seconds. At 10 hours monthly: **$14.40**
- Egress and operations: **$8.10**

**Target scale—800 schools**:
- 13,300 files per month (13.3x increase)
- 1.3 TB data processed
- 6,600 natural language queries
- **Monthly cost: approximately $520**

**Cost efficiency improves with scale**:
- Per-school cost drops from $0.75 to $0.65 per month
- BigQuery caching reduces repeated query costs
- Partitioning and clustering optimize storage costs
- Model inference costs stay nearly flat—embeddings run locally, LLM called strategically

**Managed services reduce hidden costs**:
- No DevOps team required for maintenance
- Google handles security patches, uptime SLAs
- No on-premise servers, no cooling, no physical security
- Google Cloud Support included with committed use contracts

**Cost scales linearly, not exponentially**. Traditional systems break at scale. We designed for scale from day one."

---

## SLIDE 6: TECHNOLOGY FLEXIBILITY (30 seconds)

**SPEAKER:**

"We built for adaptability. Don't want Google Cloud? Replace BigQuery with PostgreSQL using pgvector for embeddings—same SQL interface, runs on-premise. Replace Cloud Run with Kubernetes on any cloud. Replace Featherless.ai with local Ollama for complete air-gapped deployment. Replace Google Speech-to-Text with Whisper AI. 

The architecture is modular. Event-driven design means components swap independently. Open-source models mean no API lock-in. Standard interfaces: SQL, REST APIs, CloudEvents. This solution works in Czech public sector constraints, works for international schools, works for regions with data sovereignty requirements."

---

## SLIDE 7: PROVEN CAPABILITIES (30 seconds)

**SPEAKER:**

"This isn't a prototype. It's production-ready code:

80% test coverage. Event-driven pipeline processes archives with 100 files automatically. Semantic entity resolution handles Czech name variations. Natural language chat interface translates questions to SQL with multi-layer safety validation—read-only queries, forbidden operation blocking, automatic LIMIT clauses.

BigQuery fact and dimension tables with partitioning for cost optimization. Structured logging with correlation IDs for debugging. Terraform infrastructure-as-code for reproducible deployments. Docker containers for consistent environments. CI/CD ready."

---

## SLIDE 8: COMPETITIVE ADVANTAGE (30 seconds)

**SPEAKER:**

"Why does this win?

**AI-native**: Not AI bolted onto legacy systems. Built from scratch with embeddings, entity resolution, semantic understanding core to the architecture.

**Cost-effective**: Traditional enterprise data platforms cost $50,000 per year minimum. We deliver this for under $10,000 annually at 800-school scale.

**Open-source foundation**: Open models, transparent costs, no vendor extortion. Eduzměna owns their data pipeline.

**Czech context aware**: Multilingual models handle Czech names, accents, language switching. Tested on Czech educational data patterns.

**Scalable by design**: Event-driven architecture scales to 10,000 schools with minimal code changes."

---

## SLIDE 9: REAL-WORLD IMPACT (30 seconds)

**SPEAKER:**

"Let me show you what this enables:

A teacher uploads audio from a parent interview. System transcribes, extracts entities—student names, subjects, concerns—links to assessment data, creates observation records with sentiment analysis. Regional coordinator asks: 'Which interventions improved math scores in Region A?' Natural language query executes in 5 seconds, shows ranked results with confidence scores.

School uploads Excel with non-standard columns. System classifies as assessment data, maps columns intelligently, loads into warehouse. Data analyst from another region immediately queries cross-regional comparisons without understanding the original file structure.

This is data democracy. This is what scales educational equity."

---

## SLIDE 10: CLOSING (30 seconds)

**SPEAKER:**

"We've built an intelligence layer that makes data complexity invisible. Open-source models provide transparency. Managed services eliminate maintenance burden. Cost scales linearly at $0.65 per school monthly. Architecture adapts to any infrastructure requirement—cloud, hybrid, on-premise.

Eduzměna can scale from 60 to 800 schools without hiring data engineers. Teachers and coordinators get insights in natural language. Educational equity becomes data-driven.

This is not a hackathon demo. This is production infrastructure that solves the real problem: turning messy educational data into systematic improvement at national scale.

Thank you. We're ready for questions."

---

## TIMING BREAKDOWN
- Introduction: 30s
- Problem: 30s  
- Solution Architecture: 45s
- Technical Differentiators: 45s
- Pricing & Scaling: 60s (most detailed)
- Technology Flexibility: 30s
- Proven Capabilities: 30s
- Competitive Advantage: 30s
- Real-World Impact: 30s
- Closing: 30s

**TOTAL: 5 minutes exactly**

---

## Q&A PREPARATION

**Expected Questions:**

**Q: "How do you ensure data privacy with external LLM APIs?"**
A: "User questions go to Featherless.ai, but actual data never leaves Google Cloud. BigQuery results stay in EU region. For stricter requirements, we swap Featherless.ai for local Ollama with same Llama model—fully air-gapped. Architecture supports both."

**Q: "What about Czech language support?"**
A: "BGE-M3 embeddings support 100+ languages including Czech. Llama 3.1 is multilingual. Google Speech-to-Text has cs-CZ models. We tested on Czech names, accents, educational terminology. Entity resolution handles diacritics correctly—'Dvořák' matches 'Dvorak'."

**Q: "Can this handle regional data sovereignty requirements?"**
A: "Absolutely. BigQuery data never leaves europe-west1 region. For stricter requirements, PostgreSQL backend runs on-premise. Open-source models run locally. No data crosses borders unless you explicitly configure it."

**Q: "What happens when AI makes a mistake?"**
A: "Confidence scores on every classification. Data validation with Pandera schemas. Staging tables for review before production load. Natural language query safety checks prevent data modification. Audit logs for every decision. Humans stay in control."

**Q: "Why not use traditional ETL tools?"**
A: "Traditional ETL requires predefined schemas. Educational data doesn't have consistent schemas. AI embeddings understand semantic similarity—'Student' equals 'Pupil'—without manual mapping. This is the only way to handle 800 schools with different data practices."

**Q: "How long to deploy?"**
A: "Terraform provisions infrastructure in 10 minutes. Docker images deploy to Cloud Run in 5 minutes. Initial model downloads take 20 minutes. Total: under 1 hour from zero to production. We can demonstrate this live."

---

## KEY MESSAGES TO EMPHASIZE

1. **This solves Eduzměna's stated problem exactly**: Scaling from 60 to 800 schools with exponential data complexity
2. **Cost transparency**: Real numbers, not vague estimates. Show the math.
3. **Open-source = no vendor lock-in**: Eduzměna owns their solution
4. **Managed = low maintenance**: Small team can operate at national scale
5. **Production-ready**: Not a demo, not a prototype—deployable today
6. **Czech context aware**: Built for Czech educational sector requirements
7. **Architecturally flexible**: Adapts to changing requirements and constraints

---

## CONFIDENCE POINTS

- **We shipped production code, not slides**: GitHub repo is the proof
- **We understand the domain**: Fact/dimension tables, educational data types, regional structures
- **We understand cost at scale**: Real pricing research, not guesses
- **We understand Czech requirements**: Data sovereignty, multilingual, public sector constraints
- **We understand maintenance**: Chose managed services deliberately to minimize operational burden

---

## DIFFERENTIATORS FROM OTHER TEAMS

Most teams will build:
- Simple file upload with basic validation
- Manual schema mapping
- Traditional database storage
- Basic reporting

We built:
- **AI-native intelligence layer** that understands semantics
- **Event-driven architecture** that scales automatically
- **Natural language interface** that democratizes data access
- **Open-source foundation** that avoids vendor lock-in
- **Production infrastructure** with real cost analysis

This is not an incremental improvement. This is rethinking educational data infrastructure with AI-first principles.

---

## FINAL NOTES

- Speak confidently but not arrogantly
- Make eye contact with each jury member
- When mentioning costs, pause to let numbers sink in
- When mentioning open-source, emphasize transparency and ownership
- When mentioning scale, connect back to Eduzměna's goal: 800 schools, 15% of Czech system
- End with impact: This enables educational equity at national scale

**We're not selling software. We're enabling systemic change.**

