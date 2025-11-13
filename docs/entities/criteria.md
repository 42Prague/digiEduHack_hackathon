# Criteria

## Overview
Represents a measurement standard or key performance indicator (KPI) important to the education system. Criteria are tracked per region and used to evaluate experiment success and overall system performance.

## Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `name` | String | Yes | Criteria name (e.g., "Student Satisfaction Score") |
| `description` | String | Yes | Detailed explanation of what is measured |
| `measurement_unit` | String | Yes | Unit of measurement (e.g., "percentage", "score_0_100") |
| `calculation_method` | String | Yes | How the metric is calculated |
| `target_value` | Float | No | Desired target value for this criteria |
| `valid_from` | DateTime | Yes | When this criteria definition became active |
| `valid_to` | DateTime | No | When this criteria definition became inactive (NULL = currently active) |
| `metadata` | JSON | No | Additional attributes (data sources, frequency) |

### Metadata Schema (Example)
```json
{
  "category": "student_outcomes",
  "priority": "high",
  "data_source": "student_feedback",
  "collection_frequency": "monthly",
  "aggregation_method": "weighted_average",
  "benchmark_value": 75.0,
  "interpretation": {
    "excellent": "> 85",
    "good": "70-85",
    "needs_improvement": "< 70"
  },
  "related_criteria": ["teacher_effectiveness", "curriculum_quality"]
}
```

## Methods

### `evaluate()`
Calculates current value of this criteria for a given region.

**Returns:** `Float`

**Example Logic:**
```python
def evaluate(self, region_id, timestamp):
    if self.name == "Student Satisfaction Score":
        # Calculate average student feedback sentiment
        feedbacks = get_student_feedbacks(region_id, timestamp)
        return (sum(f.sentiment_score for f in feedbacks) / len(feedbacks)) * 100
    elif self.name == "Teacher Retention Rate":
        # Calculate percentage of teachers staying
        teachers_start = count_teachers(region_id, timestamp - timedelta(days=365))
        teachers_end = count_teachers(region_id, timestamp)
        return (teachers_end / teachers_start) * 100
```

## Relationships

- **Measured in** many `Region` through `RegionCriteria` (many-to-many)
- **Evaluated in** many `Experiment` through `ExperimentCriteria` (many-to-many)
- **Evaluated by** many `Feedback` (implicit - feedback contributes to criteria)

## Temporal Behavior

Criteria definitions can evolve:
- **Calculation change**: Create new criteria version with updated `calculation_method`
- **Target adjustment**: Create new version with updated `target_value`
- **Deprecation**: Set `valid_to` to stop tracking

Example: Update target value for student satisfaction
```sql
-- Close old criteria definition
UPDATE Criteria SET valid_to = CURRENT_TIMESTAMP
WHERE id = :criteria_id AND valid_to IS NULL;

-- Create new version
INSERT INTO Criteria (id, name, description, target_value, valid_from, ...)
VALUES (:criteria_id, :name, :description, :new_target, CURRENT_TIMESTAMP, ...);
```

## Use Cases

### UC1: Regional Performance Dashboard
Show all criteria values for a region:
```sql
SELECT
  c.name,
  c.measurement_unit,
  rc.baseline_value,
  c.target_value,
  c.evaluate(r.id, CURRENT_TIMESTAMP) as current_value,
  CASE
    WHEN c.evaluate(r.id, CURRENT_TIMESTAMP) >= c.target_value THEN 'Target Met'
    ELSE 'Below Target'
  END as status
FROM Region r
JOIN RegionCriteria rc ON r.id = rc.region_id
JOIN Criteria c ON rc.criteria_id = c.id
WHERE r.id = :region_id
  AND rc.valid_to IS NULL
  AND c.valid_to IS NULL
```

### UC2: Criteria Improvement Tracking
Track how criteria values change over time:
```sql
SELECT
  DATE_TRUNC('month', f.timestamp) as month,
  AVG(f.sentiment_score) * 100 as criteria_value
FROM Criteria c
JOIN RegionCriteria rc ON c.id = rc.criteria_id
JOIN Feedback f ON f.related_criteria_ids @> ARRAY[c.id]
WHERE c.id = :criteria_id
  AND rc.region_id = :region_id
  AND f.timestamp >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', f.timestamp)
ORDER BY month
```

### UC3: Cross-Regional Comparison
Compare regions on specific criteria:
```sql
SELECT
  r.name as region,
  c.name as criteria,
  c.evaluate(r.id, CURRENT_TIMESTAMP) as current_value,
  rc.baseline_value,
  c.evaluate(r.id, CURRENT_TIMESTAMP) - rc.baseline_value as improvement,
  RANK() OVER (ORDER BY c.evaluate(r.id, CURRENT_TIMESTAMP) DESC) as rank
FROM Region r
JOIN RegionCriteria rc ON r.id = rc.region_id
JOIN Criteria c ON rc.criteria_id = c.id
WHERE c.id = :criteria_id
  AND r.valid_to IS NULL
  AND rc.valid_to IS NULL
ORDER BY current_value DESC
```

### UC4: Experiment Success Measurement
Evaluate if experiment improved targeted criteria:
```sql
SELECT
  e.name as experiment,
  c.name as criteria,
  AVG(CASE WHEN f.timestamp < e.start_date THEN f.sentiment_score END) as before_value,
  AVG(CASE WHEN f.timestamp BETWEEN e.start_date AND e.end_date THEN f.sentiment_score END) as during_value,
  AVG(CASE WHEN f.timestamp > e.end_date THEN f.sentiment_score END) as after_value
FROM Experiment e
JOIN ExperimentCriteria ec ON e.id = ec.experiment_id
JOIN Criteria c ON ec.criteria_id = c.id
JOIN Feedback f ON c.id = ANY(f.related_criteria_ids)
WHERE e.id = :experiment_id
GROUP BY e.name, c.name
```

## Data Privacy

- **Storage**: EU-only (Google Cloud europe-west1)
- **PII**: None - criteria are aggregate metrics
- **Access**: Public within the education system
- **GDPR**: Not applicable (no personal data)

## Validation Rules

- `name` should be unique per active criteria
- `measurement_unit` must be one of predefined units
- `calculation_method` must be documented and reproducible
- `target_value` must be realistic given `measurement_unit`
- Cannot delete criteria if used in active experiments
- Cannot have overlapping active versions (check `valid_from`/`valid_to`)

## BigQuery Schema

```sql
CREATE TABLE criteria (
  id STRING NOT NULL,
  name STRING NOT NULL,
  description STRING NOT NULL,
  measurement_unit STRING NOT NULL,
  calculation_method STRING NOT NULL,
  target_value FLOAT64,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  metadata JSON,
  _created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  _updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(valid_from)
CLUSTER BY name;
```

## Sample Data

```json
{
  "id": "a50e8400-e29b-41d4-a716-446655440005",
  "name": "Student Satisfaction Score",
  "description": "Average sentiment score from student feedback on learning experience",
  "measurement_unit": "percentage",
  "calculation_method": "AVG(student_feedback.sentiment_score) * 100, where sentiment_score ranges from -1.0 to 1.0",
  "target_value": 75.0,
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_to": null,
  "metadata": {
    "category": "student_outcomes",
    "priority": "high",
    "data_source": "student_feedback",
    "collection_frequency": "monthly",
    "aggregation_method": "weighted_average",
    "benchmark_value": 75.0,
    "interpretation": {
      "excellent": "> 85",
      "good": "70-85",
      "needs_improvement": "< 70"
    }
  }
}
```

## Standard Criteria Categories

### Student Outcomes
- Student Satisfaction Score
- Academic Performance Index
- Attendance Rate
- Dropout Rate
- College Readiness Score

### Teacher Effectiveness
- Teacher Satisfaction Score
- Professional Development Hours
- Teacher Retention Rate
- Student-Teacher Feedback Alignment

### Operational Efficiency
- Resource Utilization Rate
- Administrative Efficiency Index
- Technology Adoption Rate
- Parent Engagement Level

### Compliance & Quality
- Rule Compliance Rate
- Data Quality Score
- Curriculum Coverage Rate
- Safety Incident Rate
