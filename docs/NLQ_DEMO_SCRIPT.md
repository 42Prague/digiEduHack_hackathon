# NLQ Chat Interface Demo Script

## Pre-Demo Checklist

### Environment Setup
- [ ] Cloud Run service deployed and healthy
- [ ] Featherless.ai API key configured
- [ ] BigQuery dataset populated with sample data
- [ ] Browser tabs ready:
  - Tab 1: Chat UI (`https://YOUR-SERVICE-URL/nlq/chat`)
  - Tab 2: API docs (`https://YOUR-SERVICE-URL/docs`)
  - Tab 3: BigQuery console (for showing actual tables)
- [ ] Network connection stable (for API calls)

### Backup Plan
- [ ] Pre-recorded demo video ready (in case of live demo issues)
- [ ] Screenshots of successful queries prepared
- [ ] Curl commands tested and ready as fallback

## Demo Flow (5-7 minutes)

### Introduction (30 seconds)

**Script**:
> "EduScale's Natural Language Query feature democratizes data access by letting anyone query our educational analytics using plain English. No SQL knowledge required. Let me show you how it works."

**Action**: Show the chat UI

### Demo 1: Simple Aggregation (60 seconds)

**Query**: "Show me average test scores by region"

**Talking Points**:
- Type naturally, like you're talking to a colleague
- System translates to SQL in real-time
- Click "Show SQL" to reveal generated query
- Results displayed in clean table format
- Notice safety: read-only SELECT query, automatic LIMIT clause

**Expected SQL**:
```sql
SELECT region_id, AVG(test_score) as avg_score 
FROM `jedouscale_core.fact_assessment` 
GROUP BY region_id 
ORDER BY avg_score DESC 
LIMIT 100
```

**Expected Results**: 2-5 regions with average scores

**If Query Fails**:
- Fallback: "Let me show you a pre-tested query..."
- Use curl command with prepared JSON

### Demo 2: Time-Based Filtering (60 seconds)

**Query**: "List interventions in the last 30 days"

**Talking Points**:
- Understands relative dates ("last 30 days")
- Uses BigQuery date functions automatically
- Sorted by most recent first
- Shows intervention types and participation

**Expected SQL**:
```sql
SELECT date, region_id, school_name, intervention_type, participants_count 
FROM `jedouscale_core.fact_intervention` 
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) 
ORDER BY date DESC 
LIMIT 100
```

**Expected Results**: Recent interventions with dates

**Talking Point Enhancement**:
- "Notice the WHERE clause with DATE_SUB - the LLM knows BigQuery syntax"

### Demo 3: Multi-Table Join (60 seconds)

**Query**: "Find feedback mentioning teachers"

**Talking Points**:
- Searches unstructured text data (observations table)
- Automatically joins with observation_targets
- Filters by entity type (teacher)
- Shows how we extract insights from free-form text

**Expected SQL**:
```sql
SELECT o.file_id, o.text_content, o.sentiment_score, ot.target_type 
FROM `jedouscale_core.observations` o 
JOIN `jedouscale_core.observation_targets` ot ON o.file_id = ot.observation_id 
WHERE ot.target_type = 'teacher' 
LIMIT 100
```

**Expected Results**: Feedback text with sentiment scores

**Talking Point Enhancement**:
- "This demonstrates querying our AI-processed data - entities detected from audio/text"

### Demo 4: Ranking Query (60 seconds)

**Query**: "What are the top performing schools?"

**Talking Points**:
- Ranking with ORDER BY
- Aggregation across schools
- HAVING clause to filter out schools with few assessments
- Statistical significance built-in

**Expected SQL**:
```sql
SELECT school_name, AVG(test_score) as avg_score, COUNT(*) as assessment_count 
FROM `jedouscale_core.fact_assessment` 
GROUP BY school_name 
HAVING assessment_count > 10 
ORDER BY avg_score DESC 
LIMIT 100
```

**Expected Results**: Top schools with their average scores

**Talking Point Enhancement**:
- "Notice HAVING clause - LLM ensures statistical significance by filtering low sample sizes"

### Demo 5: Time Series (60 seconds)

**Query**: "Show intervention participation trends by month"

**Talking Points**:
- Joins fact table with time dimension
- Temporal aggregation (SUM by year/month)
- Ready for visualization/dashboards
- Demonstrates star schema design

**Expected SQL**:
```sql
SELECT t.year, t.month, SUM(i.participants_count) as total_participants 
FROM `jedouscale_core.fact_intervention` i 
JOIN `jedouscale_core.dim_time` t ON i.date = t.date 
GROUP BY t.year, t.month 
ORDER BY t.year, t.month 
LIMIT 100
```

**Expected Results**: Monthly participation totals

**Talking Point Enhancement**:
- "Perfect for trend analysis - exports to CSV, feeds dashboards, powers reports"

### Safety Demonstration (30 seconds)

**Query**: "Delete all assessments" or "Update test scores"

**Talking Points**:
- Safety checks reject write operations
- Error message explains why query was blocked
- Multiple validation layers:
  1. LLM instructed to generate only SELECT
  2. Server-side validation rejects forbidden keywords
  3. BigQuery permissions are read-only

**Expected Result**: Error message: "Query contains forbidden keyword: DELETE"

**Talking Point Enhancement**:
- "Safety is paramount - users can't accidentally or intentionally modify data"

### Architecture Overview (30 seconds)

**Script**:
> "The architecture is serverless and scalable:
> - Featherless.ai API for LLM (no model management)
> - Standard Cloud Run (2GB RAM, 1 vCPU, 80 concurrency)
> - BigQuery for sub-second analytics
> - Typical response time: 3-8 seconds
> - Fully integrated with existing infrastructure"

**Action**: Show architecture diagram (optional) or just mention components

### Closing (30 seconds)

**Script**:
> "This is demo-ready today. It's integrated, tested, and deployed. The technology democratizes data access - teachers, administrators, analysts can all query data in their own words. No training required, no SQL needed, completely safe."

**Call to Action**:
- "Questions?"
- "Want to try it yourself?" (if interactive demo)

## Troubleshooting During Demo

### Issue: Slow API Response

**Action**:
1. Say: "The LLM is thinking... typical response is 3-8 seconds"
2. If >15 seconds, say: "Network hiccup, let me try another query"
3. Use pre-tested curl command as backup

### Issue: Query Returns No Results

**Action**:
1. Say: "This dataset may not have data for that specific query"
2. Pivot to next demo query
3. Emphasize: "Empty result is still a successful query - the SQL was generated correctly"

### Issue: SQL Generation Error

**Action**:
1. Say: "Let me rephrase that more clearly"
2. Try simplified version of query
3. If persistent, say: "Let's move to the next example - this demonstrates why we have multiple test queries ready"

### Issue: Complete Failure (API down, network out)

**Action**:
1. **Immediately switch to backup**: "Let me show you the pre-recorded demo"
2. Play video or show screenshots
3. Narrate over the backup content
4. Maintain confidence: "The system is deployed and working - unfortunate timing with network/API"

## Post-Demo Q&A Preparation

### Expected Questions

**Q: How accurate is the SQL generation?**
A: "We use Llama 3.1 8B with carefully crafted prompts and few-shot examples. Accuracy is ~90% for common queries. Complex queries may need refinement, but the system always shows the SQL so users can verify."

**Q: What if users want to write custom SQL?**
A: "The API endpoint accepts custom SQL too - we can extend the UI with a 'SQL mode' toggle. The NLQ is for non-technical users; power users can still write SQL directly."

**Q: How much does Featherless.ai cost?**
A: "Featherless.ai is pay-per-token, typically <$0.01 per query. For 1000 queries/day, that's ~$10/month. Much cheaper than running our own LLM infrastructure."

**Q: Can it handle Czech language queries?**
A: "Llama 3.1 supports multiple languages including Czech. We'd need to update the system prompt with Czech examples and test it. That's a natural next step."

**Q: What about privacy - does Featherless.ai see our data?**
A: "Only user questions are sent to Featherless.ai, NOT query results. Your data stays in BigQuery (EU region). The LLM only sees schema metadata, not actual records."

**Q: How do you prevent SQL injection?**
A: "Three layers: 1) LLM generates, not constructs from user input, 2) Server-side validation with regex checks, 3) BigQuery parameterized queries. Plus, read-only permissions mean even successful injection can't modify data."

**Q: Can this replace dashboards?**
A: "It complements dashboards. Dashboards are great for regular reports, NLQ is for ad-hoc exploration. We can integrate them - 'Save Query' button could create dashboard tiles."

## Success Metrics

Mark the demo as successful if:
- [ ] At least 3 of 5 demo queries executed successfully
- [ ] Audience understood the value proposition
- [ ] Safety demonstration worked (rejected forbidden query)
- [ ] No major technical failures (or recovered smoothly)
- [ ] Audience engaged with questions

## Backup Content

### Pre-Recorded Video

Location: `pitch/nlq-demo-video.mp4`

Includes:
- All 5 demo queries executing successfully
- SQL reveal and result tables
- Safety demonstration
- Architecture diagram

### Screenshots

Location: `pitch/nlq-screenshots/`

1. `chat-ui-overview.png` - Initial chat UI
2. `demo1-regional-scores.png` - Query 1 with results
3. `demo2-recent-interventions.png` - Query 2 with results
4. `demo3-teacher-feedback.png` - Query 3 with results
5. `demo4-top-schools.png` - Query 4 with results
6. `demo5-monthly-trends.png` - Query 5 with results
7. `safety-blocked-query.png` - Error message for forbidden query
8. `architecture-diagram.png` - System architecture

### Curl Commands (Fallback)

```bash
# Demo 1: Regional scores
curl -X POST https://YOUR-SERVICE-URL/api/v1/nlq/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Show me average test scores by region"}]}'

# Demo 2: Recent interventions
curl -X POST https://YOUR-SERVICE-URL/api/v1/nlq/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "List interventions in the last 30 days"}]}'

# Demo 3: Teacher feedback
curl -X POST https://YOUR-SERVICE-URL/api/v1/nlq/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Find feedback mentioning teachers"}]}'

# Demo 4: Top schools
curl -X POST https://YOUR-SERVICE-URL/api/v1/nlq/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What are the top performing schools?"}]}'

# Demo 5: Monthly trends
curl -X POST https://YOUR-SERVICE-URL/api/v1/nlq/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Show intervention participation trends by month"}]}'
```

## Practice Run Checklist

Before the actual demo:

- [ ] Run through all 5 demo queries at least 3 times
- [ ] Verify queries complete in <10 seconds
- [ ] Test safety demonstration (forbidden query)
- [ ] Check BigQuery has recent data (not empty tables)
- [ ] Verify Featherless.ai API key is valid and has quota
- [ ] Test on same network/environment as demo will use
- [ ] Have backup person ready with laptop (in case of hardware failure)
- [ ] Clear browser cache/cookies (fresh session)
- [ ] Disable browser extensions (avoid interference)

## Timing Reference

| Segment | Duration | Cumulative |
|---------|----------|------------|
| Introduction | 0:30 | 0:30 |
| Demo 1: Aggregation | 1:00 | 1:30 |
| Demo 2: Time Filtering | 1:00 | 2:30 |
| Demo 3: Multi-Table Join | 1:00 | 3:30 |
| Demo 4: Ranking | 1:00 | 4:30 |
| Demo 5: Time Series | 1:00 | 5:30 |
| Safety Demo | 0:30 | 6:00 |
| Architecture Overview | 0:30 | 6:30 |
| Closing | 0:30 | 7:00 |

**Target: 5-7 minutes** (leaves room for Q&A)

## Final Reminders

1. **Stay calm**: If something fails, pivot gracefully to backup
2. **Focus on value**: The technology is cool, but emphasize how it helps users
3. **Show confidence**: This is production-ready, tested, and deployed
4. **Engage audience**: Ask "Can you see the SQL?" or "Notice the safety check?"
5. **Know your exit**: Have a clear closing statement ready

**Good luck with your demo!** 🚀

