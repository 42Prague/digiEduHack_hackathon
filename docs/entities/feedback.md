# Feedback

## Overview
Represents qualitative and quantitative input from stakeholders (students, teachers, parents) about their educational experiences. Feedback is the primary mechanism for measuring criteria, evaluating experiments, and understanding system performance.

## Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `author_id` | UUID | Yes | ID of the person providing feedback |
| `author_type` | String | Yes | Type: `student`, `teacher`, `parent` |
| `target_entity_id` | UUID | No | ID of entity being evaluated (optional) |
| `target_entity_type` | String | No | Type: `region`, `school`, `teacher`, `subject`, `rule` |
| `timestamp` | DateTime | Yes | When feedback was provided |
| `sentiment_score` | Float | Yes | Normalized sentiment: -1.0 (negative) to +1.0 (positive) |
| `category` | String | Yes | Feedback category (e.g., `teaching_quality`, `curriculum`) |
| `text_content` | String | No | Optional free-text feedback |
| `structured_data` | JSON | No | Structured survey responses or ratings |
| `experiment_id` | UUID | No | Link to experiment if feedback is part of one |
| `related_criteria_ids` | List\<UUID\> | No | Criteria this feedback contributes to |

### Structured Data Schema (Example)
```json
{
  "survey_id": "student_satisfaction_q1_2024",
  "responses": [
    {
      "question": "How satisfied are you with the teaching quality?",
      "answer": "Very satisfied",
      "rating": 5,
      "scale": "1-5"
    },
    {
      "question": "Do you feel supported by your teacher?",
      "answer": "Yes",
      "rating": 4,
      "scale": "1-5"
    }
  ],
  "completion_time_seconds": 180,
  "device_type": "mobile"
}
```

## Methods

### `analyze()`
Performs sentiment analysis and extracts structured insights from text_content.

**Returns:** `AnalysisResult`

**Example Logic:**
```python
def analyze(self):
    if self.text_content:
        # Use NLP to extract topics and sentiment
        topics = extract_topics(self.text_content)
        refined_sentiment = calculate_sentiment(self.text_content)
        keywords = extract_keywords(self.text_content)

        return {
            'topics': topics,
            'refined_sentiment': refined_sentiment,
            'keywords': keywords,
            'requires_attention': refined_sentiment < -0.6
        }
    return None
```

## Relationships

- **Provided by** one `Student`, `Teacher`, or `Parent` (polymorphic many-to-one)
- **Targets** one entity (polymorphic many-to-one, optional)
- **Relates to** one `Experiment` (many-to-one, optional)
- **Evaluates** many `Criteria` (many-to-many through `related_criteria_ids`)

## Temporal Behavior

Feedback is immutable once submitted:
- **No updates**: Feedback cannot be edited after submission
- **No deletion**: Feedback is permanent for audit trail
- **Timestamp critical**: Used for before/after experiment analysis

## Use Cases

### UC1: Real-Time Sentiment Dashboard
Monitor current sentiment across regions:
```sql
SELECT
  r.name as region,
  f.category,
  COUNT(f.id) as feedback_count,
  AVG(f.sentiment_score) as avg_sentiment,
  STDDEV(f.sentiment_score) as sentiment_variation
FROM Feedback f
JOIN Student s ON f.author_id = s.id AND f.author_type = 'student'
JOIN Region r ON s.current_region_id = r.id
WHERE f.timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY r.name, f.category
ORDER BY avg_sentiment ASC
```

### UC2: Teacher Performance Evaluation
Aggregate feedback for individual teachers:
```sql
SELECT
  t.name as teacher,
  sub.name as subject,
  COUNT(f.id) as feedback_count,
  AVG(f.sentiment_score) as avg_sentiment,
  COUNT(CASE WHEN f.sentiment_score < -0.5 THEN 1 END) as negative_feedback_count,
  STRING_AGG(DISTINCT f.category, ', ') as feedback_categories
FROM Teacher t
JOIN StudentTeacherSubject sts ON t.id = sts.teacher_id
JOIN Subject sub ON sts.subject_id = sub.id
LEFT JOIN Feedback f ON f.target_entity_id = t.id
  AND f.target_entity_type = 'teacher'
  AND f.timestamp BETWEEN sts.valid_from AND COALESCE(sts.valid_to, CURRENT_TIMESTAMP)
WHERE sts.valid_to IS NULL
GROUP BY t.id, t.name, sub.name
```

### UC3: Criteria Calculation
Calculate criteria values from aggregated feedback:
```sql
SELECT
  c.name as criteria,
  r.name as region,
  AVG(f.sentiment_score) * 100 as criteria_score,
  COUNT(f.id) as sample_size,
  MIN(f.sentiment_score) * 100 as min_score,
  MAX(f.sentiment_score) * 100 as max_score
FROM Criteria c
JOIN RegionCriteria rc ON c.id = rc.criteria_id
JOIN Region r ON rc.region_id = r.id
JOIN Feedback f ON c.id = ANY(f.related_criteria_ids)
  AND f.target_entity_type = 'region'
  AND f.target_entity_id = r.id
WHERE f.timestamp >= CURRENT_DATE - INTERVAL '30 days'
  AND rc.valid_to IS NULL
GROUP BY c.name, r.name
```

### UC4: Anomaly Detection
Identify sudden sentiment drops requiring attention:
```sql
WITH weekly_sentiment AS (
  SELECT
    target_entity_id,
    target_entity_type,
    DATE_TRUNC('week', timestamp) as week,
    AVG(sentiment_score) as avg_sentiment
  FROM Feedback
  WHERE timestamp >= CURRENT_DATE - INTERVAL '8 weeks'
  GROUP BY target_entity_id, target_entity_type, DATE_TRUNC('week', timestamp)
),
sentiment_changes AS (
  SELECT
    target_entity_id,
    target_entity_type,
    week,
    avg_sentiment,
    LAG(avg_sentiment) OVER (PARTITION BY target_entity_id, target_entity_type ORDER BY week) as prev_sentiment,
    avg_sentiment - LAG(avg_sentiment) OVER (PARTITION BY target_entity_id, target_entity_type ORDER BY week) as sentiment_change
  FROM weekly_sentiment
)
SELECT
  target_entity_type,
  target_entity_id,
  week,
  avg_sentiment,
  prev_sentiment,
  sentiment_change,
  'ALERT: Significant sentiment drop' as flag
FROM sentiment_changes
WHERE sentiment_change < -0.3
  AND week >= CURRENT_DATE - INTERVAL '2 weeks'
ORDER BY sentiment_change ASC
```

### UC5: Multi-Stakeholder Perspective
Compare perspectives of students, teachers, and parents on same target:
```sql
SELECT
  f.target_entity_type,
  f.target_entity_id,
  f.author_type,
  COUNT(f.id) as feedback_count,
  AVG(f.sentiment_score) as avg_sentiment,
  STRING_AGG(DISTINCT f.category, ', ') as categories
FROM Feedback f
WHERE f.target_entity_id = :target_id
  AND f.target_entity_type = :target_type
  AND f.timestamp >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY f.target_entity_type, f.target_entity_id, f.author_type
ORDER BY f.author_type
```

## Data Privacy

- **Storage**: EU-only (Google Cloud europe-west1)
- **PII**: CRITICAL - contains author_id and potentially identifying text_content
- **Pseudonymization**: Production systems MUST pseudonymize text_content
- **Access**:
  - Authors can see their own feedback
  - Teachers can see feedback about themselves (aggregated, not individual)
  - Admins can see aggregated feedback for their region
  - Researchers can access anonymized feedback for analysis
- **GDPR**:
  - Right to access: Export all feedback by author_id
  - Right to erasure: Anonymize author_id and redact text_content
  - Right to rectification: Feedback is immutable; only metadata can be updated

## Validation Rules

- `author_type` must be one of: `student`, `teacher`, `parent`
- `author_id` must reference existing entity of type `author_type`
- `sentiment_score` must be between -1.0 and +1.0
- `timestamp` cannot be in the future
- `target_entity_id` and `target_entity_type` must both be provided or both be NULL
- If `target_entity_id` provided, must reference existing entity of `target_entity_type`
- `category` must be from predefined category list
- Cannot delete feedback (immutable audit trail)

## BigQuery Schema

```sql
CREATE TABLE feedback (
  id STRING NOT NULL,
  author_id STRING NOT NULL,
  author_type STRING NOT NULL,
  target_entity_id STRING,
  target_entity_type STRING,
  timestamp TIMESTAMP NOT NULL,
  sentiment_score FLOAT64 NOT NULL,
  category STRING NOT NULL,
  text_content STRING,
  structured_data JSON,
  experiment_id STRING,
  related_criteria_ids ARRAY<STRING>,
  _created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY author_type, target_entity_type, category;

-- Sentiment constraint
ALTER TABLE feedback ADD CONSTRAINT check_sentiment_range
  CHECK (sentiment_score BETWEEN -1.0 AND 1.0);

-- Author type constraint
ALTER TABLE feedback ADD CONSTRAINT check_author_type
  CHECK (author_type IN ('student', 'teacher', 'parent'));

-- PII protection: Restrict direct access to text_content
CREATE ROW ACCESS POLICY feedback_privacy ON feedback
GRANT TO ('analyst@project.iam.gserviceaccount.com')
FILTER USING (text_content IS NULL OR LENGTH(text_content) = 0);
```

## Sample Data (Development Only)

```json
{
  "id": "c50e8400-e29b-41d4-a716-446655440007",
  "author_id": "550e8400-e29b-41d4-a716-446655440000",
  "author_type": "student",
  "target_entity_id": "750e8400-e29b-41d4-a716-446655440002",
  "target_entity_type": "teacher",
  "timestamp": "2024-03-15T14:30:00Z",
  "sentiment_score": 0.85,
  "category": "teaching_quality",
  "text_content": "Teacher explains concepts very clearly and is always willing to help",
  "structured_data": {
    "survey_id": "student_satisfaction_q1_2024",
    "responses": [
      {
        "question": "How satisfied are you with the teaching quality?",
        "answer": "Very satisfied",
        "rating": 5,
        "scale": "1-5"
      }
    ]
  },
  "experiment_id": null,
  "related_criteria_ids": [
    "a50e8400-e29b-41d4-a716-446655440005"
  ]
}
```

## Feedback Categories

### Student Feedback Categories
- `teaching_quality` - Quality of instruction
- `curriculum_relevance` - Curriculum relevance to goals
- `classroom_environment` - Classroom atmosphere
- `learning_resources` - Quality of materials
- `teacher_support` - Teacher availability and support
- `peer_relationships` - Relationships with classmates
- `assessment_fairness` - Fairness of grading

### Teacher Feedback Categories
- `curriculum_clarity` - Curriculum guidelines clarity
- `resource_availability` - Teaching materials availability
- `student_engagement` - Student participation
- `administrative_burden` - Administrative workload
- `professional_support` - School leadership support
- `technology_tools` - Digital tools quality
- `training_needs` - Professional development needs

### Parent Feedback Categories
- `communication` - School-parent communication
- `safety` - School safety
- `curriculum` - Curriculum quality
- `facilities` - School facilities
- `teacher_quality` - Teacher effectiveness
- `student_wellbeing` - Child's well-being
- `academic_progress` - Child's academic development
- `extracurricular` - After-school programs

## Sentiment Score Interpretation

| Range | Interpretation | Action Required |
|-------|----------------|-----------------|
| 0.7 to 1.0 | Highly Positive | Maintain and replicate success |
| 0.3 to 0.7 | Positive | Monitor and sustain |
| -0.3 to 0.3 | Neutral | Investigate and improve |
| -0.7 to -0.3 | Negative | Immediate attention needed |
| -1.0 to -0.7 | Highly Negative | Urgent intervention required |
