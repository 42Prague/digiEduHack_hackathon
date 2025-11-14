# EduScale Intelligence Layer - Slide Content
## DigiEduHack 2025 Pitch Deck

---

## SLIDE 1: TITLE & TEAM

```
EduScale Intelligence Layer
Transforming Educational Data at National Scale

Team:
• DevOps Engineer + Senior Backend Developer
• Tools: Kiro, Claude Code, Cursor, ChatGPT
• Challenge: Scale Eduzměna from 60 → 800 schools
```

---

## SLIDE 2: THE PROBLEM

```
The Data Complexity Challenge

❌ Excel files with different structures
❌ Audio recordings, PDFs, archives
❌ No standard column names
   "Student Name" = "Pupil" = "Participant"
❌ Manual processing doesn't scale

Scaling to 800 schools requires AI, not humans.
```

---

## SLIDE 3: SOLUTION ARCHITECTURE

```
Event-Driven Intelligence Layer

1. ANY File Type → Automatic Processing
   • CSV, Excel, JSON, ZIP, TAR, audio, PDF

2. AI Classification → Understand Semantics
   • BGE-M3 embeddings (1024-dim, multilingual)
   • Llama 3.1 8B entity extraction

3. Smart Mapping → Canonical Schema
   • "Student" = "Pupil" = "Participant"
   • Czech name handling: "Novák" = "Novak"

4. BigQuery → Analytics-Ready Data
   • Partitioned & clustered
   • Natural language queries
```

---

## SLIDE 4: TECHNICAL DIFFERENTIATORS

```
Production-Ready Features

✓ Open-Source Models
  • Llama 3.1 8B (Featherless.ai)
  • BGE-M3 embeddings
  • paraphrase-multilingual-mpnet
  • No vendor lock-in

✓ Embedding Intelligence
  • Semantic column matching
  • Multilingual (Czech + English)
  • Entity resolution with fuzzy matching

✓ Archive Processing
  • ZIP, TAR, GZ support
  • 100 files in one upload

✓ Natural Language Queries
  • "Show average test scores by region" → SQL
  • Safety-validated, read-only

✓ Managed Infrastructure
  • Cloud Run, BigQuery, Eventarc
  • Google handles scaling & maintenance
```

---

## SLIDE 5: PRICING & SCALING

```
Transparent Cost Model

60 Schools (Current)
• 1,000 files/month, 100 GB data
• Monthly cost: ~$45
• Per-school: $0.75/month

Breakdown:
• BigQuery: $7.50 (query + storage)
• Cloud Run: $12 (compute)
• Featherless.ai: $1 (LLM API)
• Cloud Storage: $2
• Speech-to-Text: $14.40 (audio)
• Other: $8.10

800 Schools (Target Scale)
• 13,300 files/month, 1.3 TB data
• Monthly cost: ~$520
• Per-school: $0.65/month

Cost Efficiency:
✓ Per-school cost DECREASES with scale
✓ BigQuery caching reduces repeated queries
✓ No DevOps team required
✓ Google Support included

Comparison:
Traditional enterprise platforms: $50,000+/year
Our solution at 800 schools: <$10,000/year
```

---

## SLIDE 6: TECHNOLOGY FLEXIBILITY

```
Modular Architecture

Replace ANY Component:

• BigQuery → PostgreSQL + pgvector
  (on-premise deployment)

• Cloud Run → Kubernetes
  (any cloud provider)

• Featherless.ai → Ollama
  (fully air-gapped)

• Google Speech-to-Text → Whisper AI
  (open-source alternative)

Built for:
✓ Czech public sector constraints
✓ Data sovereignty requirements
✓ International deployments
✓ Hybrid cloud scenarios
```

---

## SLIDE 7: PROVEN CAPABILITIES

```
Production-Ready Code

✓ 80% test coverage
✓ Archive processing (100+ files automatically)
✓ Czech name entity resolution
✓ Natural language → SQL translation
✓ Multi-layer query safety validation
✓ BigQuery partitioning & clustering
✓ Structured logging + correlation IDs
✓ Terraform infrastructure-as-code
✓ Docker containers + CI/CD

Not a prototype. Deployable today.
```

---

## SLIDE 8: COMPETITIVE ADVANTAGE

```
Why This Solution Wins

🎯 AI-Native Architecture
Built from scratch with embeddings at core

💰 Cost-Effective
$520/month vs $50k+/year traditional platforms

🔓 Open-Source Foundation
Own your infrastructure, no vendor lock-in

🇨🇿 Czech Context Aware
Multilingual models, Czech names, accents

📈 Designed for Scale
Event-driven: 10,000 schools with minimal changes
```

---

## SLIDE 9: REAL-WORLD IMPACT

```
What This Enables

Scenario 1: Audio Interview
• Teacher uploads parent interview recording
• System: transcribe → extract entities → link to assessments
• Coordinator: "Which students were discussed?"
• Result: Instant cross-referenced insights

Scenario 2: Natural Language Query
• Regional coordinator asks:
  "Which interventions improved math scores in Region A?"
• System: translate to SQL → execute → explain
• Result: Ranked results in 5 seconds

Scenario 3: Non-Standard Excel
• School uploads file with weird column names
• System: classify → map intelligently → load
• Result: Other regions immediately query this data

Data Democracy = Educational Equity at Scale
```

---

## SLIDE 10: CLOSING

```
Intelligence Layer for National Impact

✓ Open-source transparency
✓ Managed services = minimal maintenance
✓ $0.65 per school per month at scale
✓ Adaptable to any infrastructure
✓ Production-ready today

60 → 800 schools
No data engineers required
Natural language insights for teachers
Systematic improvement at national scale

This is not a demo.
This is production infrastructure.

Questions?
```

---

## VISUAL SUGGESTIONS

### Slide 1 (Title)
- Large bold title
- Team photos or avatars (optional)
- Simple, clean design
- Eduzměna logo

### Slide 2 (Problem)
- Icons for different file types
- Red X marks for challenges
- Visualization of data chaos

### Slide 3 (Architecture)
- Flow diagram: Upload → Process → Analyze
- Icons for: files, AI models, database
- Arrows showing event flow

### Slide 4 (Differentiators)
- 5 sections with checkmarks
- Icons for: open-source, brain (AI), archive, chat, cloud
- Use color to highlight each section

### Slide 5 (Pricing)
- Two columns: 60 schools vs 800 schools
- Large numbers: $45 vs $520
- Bar chart showing cost breakdown
- Emphasize $0.65 per school

### Slide 6 (Flexibility)
- Diagram showing swappable components
- Icons for: database, cloud, AI model, speech
- Arrows indicating replacement options

### Slide 7 (Capabilities)
- Simple checklist with green checkmarks
- Code snippet (optional)
- Architecture diagram (small)

### Slide 8 (Advantage)
- 5 key points with bold icons
- Comparison table (optional)
- Cost comparison bar chart

### Slide 9 (Impact)
- 3 scenarios with illustrations
- Before/after comparison
- User personas: teacher, coordinator

### Slide 10 (Closing)
- Large key numbers
- Call to action
- Contact information
- GitHub repo link (optional)

---

## COLOR SCHEME SUGGESTIONS

- **Primary**: Deep blue (trust, technology)
- **Secondary**: Green (growth, success)
- **Accent**: Orange (innovation, energy)
- **Text**: Dark gray on white background
- **Highlights**: Bold for numbers and key terms

---

## TYPOGRAPHY SUGGESTIONS

- **Title font**: Bold, modern sans-serif (Montserrat, Inter)
- **Body font**: Clean, readable sans-serif (Open Sans, Roboto)
- **Code font**: Monospace (Fira Code, Source Code Pro)
- **Size hierarchy**: Title (48pt) > Section (32pt) > Body (24pt)

---

## ANIMATION SUGGESTIONS (MINIMAL)

- Slide transitions: Simple fade or slide from right
- Build animations: Fade in for bullet points
- Emphasis: Highlight key numbers when speaking
- **Keep it professional, not distracting**

---

## TIMING REMINDERS

- **30 seconds per slide** on average
- **60 seconds for Slide 5** (pricing detail)
- **Practice with timer** to stay exactly at 5 minutes
- **Pause after key numbers** to let them sink in
- **Make eye contact** during transitions

---

## BACKUP SLIDES (IF TIME ALLOWS)

### Technical Deep Dive
```
Architecture Details
• Event-driven: Eventarc + Cloud Run
• Models: BGE-M3 (1024-dim), Llama 3.1 8B
• Storage: Cloud Storage → BigQuery
• Processing: MIME decoder → Transformer → Tabular
```

### Cost Breakdown Table
```
Detailed Pricing (800 Schools)
BigQuery:     $96  (storage + query)
Cloud Run:    $156 (compute)
Featherless:  $13  (LLM API)
Storage:      $26  (file storage)
Speech API:   $192 (audio transcription)
Networking:   $37  (egress)
TOTAL:        $520/month = $6,240/year
```

### Security & Compliance
```
Data Protection
✓ BigQuery in EU region (europe-west1)
✓ Data never leaves EU
✓ Service accounts with least privilege
✓ Audit logs for all operations
✓ GDPR compliant
✓ Read-only query validation
```

---

## PRESENTATION BEST PRACTICES

1. **Start strong**: Immediately establish credibility
2. **Show, don't just tell**: Architecture diagrams, not walls of text
3. **Use numbers**: Specific costs, not vague estimates
4. **Tell stories**: Real scenarios, not abstract features
5. **End with impact**: National educational equity, not just technology

---

## WHAT NOT TO DO

❌ Don't read slides word-for-word
❌ Don't use technical jargon without explanation
❌ Don't go over 5 minutes (will be cut off)
❌ Don't apologize for limitations
❌ Don't dismiss other solutions
❌ Don't forget to pause for emphasis

---

## JURY-SPECIFIC MESSAGING

**Eudald Vaquer (42 Prague)**
- Emphasize: Technical excellence, modern architecture, peer learning model applicability

**Roland Maťas (Eduzměna - Evaluation)**
- Emphasize: Data quality, entity resolution, analytics capabilities

**Tomáš Kropáček (Eduzměna - SEO/Tech)**
- Emphasize: Open-source, cost efficiency, scalability

**Joe Fleming (AI Tinkerers - Featherless AI CRO)**
- Emphasize: LLM integration, prompt engineering, model selection rationale

**Matěj Bacovský (NPI - Director)**
- Emphasize: National scale impact, data-driven decision-making, public sector fit

---

## SUCCESS METRICS

After the pitch, jury should remember:
1. **$0.65 per school per month** at scale
2. **Open-source models** = no vendor lock-in
3. **AI-native** architecture, not retrofitted
4. **Production-ready** today, not a prototype
5. **800 schools** = 15% of Czech educational system

If they remember these 5 points, we win.

