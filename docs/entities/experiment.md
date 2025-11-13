# Experiment

## Overview
Represents a controlled intervention or pilot program designed to test a hypothesis about improving educational outcomes. Experiments are linked to specific criteria and regions to measure impact systematically.

## Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `name` | String | Yes | Experiment name (e.g., "Digital Learning Pilot Q1 2024") |
| `description` | String | Yes | Detailed explanation of the intervention |
| `hypothesis` | String | Yes | What improvement is expected and why |
| `start_date` | DateTime | Yes | When experiment begins |
| `end_date` | DateTime | No | When experiment ends (NULL = ongoing) |
| `status` | String | Yes | Current status: `planned`, `active`, `completed`, `cancelled` |
| `metadata` | JSON | No | Additional attributes (budget, resources, participants) |

### Metadata Schema (Example)
```json
{
  "intervention_type": "teaching_method",
  "budget": 50000,
  "currency": "EUR",
  "target_population": "grade_7_math_students",
  "sample_size": 450,
  "control_group": true,
  "control_group_size": 450,
  "principal_investigator": {
    "name": "Dr. Eva Horáková",
    "email": "eva.horakova@university.cz"
  },
  "resources_used": [
    "digital_learning_platform",
    "teacher_training_program"
  ],
  "milestones": [
    {
      "date": "2024-03-15",
      "description": "Teacher training completed",
      "status": "completed"
    },
    {
      "date": "2024-06-30",
      "description": "Mid-point evaluation",
      "status": "planned"
    }
  ]
}
```

## Methods

### `getCriteria()`
Returns all criteria being measured in this experiment.

**Returns:** `List<Criteria>`

**SQL Example:**
```sql
SELECT c.* FROM Criteria c
JOIN ExperimentCriteria ec ON c.id = ec.criteria_id
WHERE ec.experiment_id = :experiment_id
```

### `getFeedback()`
Returns all feedback collected during this experiment.

**Returns:** `List<Feedback>`

**SQL Example:**
```sql
SELECT * FROM Feedback
WHERE experiment_id = :experiment_id
  AND timestamp BETWEEN :start_date AND COALESCE(:end_date, CURRENT_TIMESTAMP)
ORDER BY timestamp DESC
```

### `calculateImpact()`
Calculates the impact of experiment on each measured criteria.

**Returns:** `Dict[Criteria, ImpactMetrics]`

**Example Logic:**
```python
def calculateImpact(self):
    results = {}
    for criteria in self.getCriteria():
        baseline = get_criteria_value_at(criteria, self.start_date - timedelta(days=30))
        current = get_criteria_value_at(criteria, self.end_date or datetime.now())

        results[criteria] = {
            'baseline': baseline,
            'current': current,
            'absolute_change': current - baseline,
            'percent_change': ((current - baseline) / baseline) * 100,
            'statistical_significance': run_statistical_test(criteria, self)
        }
    return results
```

## Relationships

- **Conducted in** many `Region` through `RegionExperiment` (many-to-many)
- **Measures** many `Criteria` through `ExperimentCriteria` (many-to-many)
- **Has** many `Feedback` (one-to-many)

## Temporal Behavior

Experiments have a clear lifecycle:
1. **planned**: Experiment designed but not yet started
2. **active**: Currently running (`start_date <= NOW < end_date`)
3. **completed**: Finished with results available
4. **cancelled**: Terminated early without completing

Status transitions:
```
planned → active → completed
planned → cancelled
active → cancelled
```

## Use Cases

### UC1: Experiment Impact Analysis
Compare criteria values before, during, and after experiment:
```sql
WITH experiment_timeline AS (
  SELECT
    e.id,
    e.name,
    e.start_date,
    e.end_date,
    c.id as criteria_id,
    c.name as criteria_name
  FROM Experiment e
  JOIN ExperimentCriteria ec ON e.id = ec.experiment_id
  JOIN Criteria c ON ec.criteria_id = c.id
  WHERE e.id = :experiment_id
)
SELECT
  et.name as experiment,
  et.criteria_name,
  AVG(CASE
    WHEN f.timestamp < et.start_date - INTERVAL '30 days'
      AND f.timestamp >= et.start_date - INTERVAL '60 days'
    THEN f.sentiment_score
  END) as baseline_value,
  AVG(CASE
    WHEN f.timestamp BETWEEN et.start_date AND COALESCE(et.end_date, CURRENT_TIMESTAMP)
    THEN f.sentiment_score
  END) as during_value,
  AVG(CASE
    WHEN f.timestamp > COALESCE(et.end_date, CURRENT_TIMESTAMP)
      AND f.timestamp <= COALESCE(et.end_date, CURRENT_TIMESTAMP) + INTERVAL '30 days'
    THEN f.sentiment_score
  END) as post_value
FROM experiment_timeline et
JOIN Feedback f ON et.criteria_id = ANY(f.related_criteria_ids)
GROUP BY et.name, et.criteria_name
```

### UC2: Cross-Experiment Comparison
Compare effectiveness of different experiments on same criteria:
```sql
SELECT
  e.name as experiment,
  c.name as criteria,
  ec.weight as criteria_weight,
  e.calculateImpact() as impact_metrics,
  r.name as region
FROM Experiment e
JOIN ExperimentCriteria ec ON e.id = ec.experiment_id
JOIN Criteria c ON ec.criteria_id = c.id
JOIN RegionExperiment re ON e.id = re.experiment_id
JOIN Region r ON re.region_id = r.id
WHERE c.id = :criteria_id
  AND e.status = 'completed'
ORDER BY impact_metrics->>'percent_change' DESC
```

### UC3: Experiment ROI Calculation
Calculate return on investment for completed experiments:
```sql
SELECT
  e.name,
  e.metadata->>'budget' as budget,
  COUNT(DISTINCT re.region_id) as regions_participated,
  COUNT(DISTINCT f.id) as feedback_collected,
  AVG(f.sentiment_score) as avg_sentiment,
  e.calculateImpact() as impact_summary,
  (e.calculateImpact()->>'percent_change')::float /
    (e.metadata->>'budget')::float as roi_score
FROM Experiment e
JOIN RegionExperiment re ON e.id = re.experiment_id
LEFT JOIN Feedback f ON f.experiment_id = e.id
WHERE e.status = 'completed'
GROUP BY e.id, e.name, e.metadata
ORDER BY roi_score DESC
```

### UC4: Experiment Replication Recommendation
Identify successful experiments worth replicating in new regions:
```sql
WITH successful_experiments AS (
  SELECT
    e.id,
    e.name,
    e.description,
    COUNT(DISTINCT re.region_id) as regions_tested,
    AVG(impact_metrics.percent_change) as avg_improvement
  FROM Experiment e
  JOIN RegionExperiment re ON e.id = re.experiment_id
  WHERE e.status = 'completed'
    AND e.calculateImpact()->>'statistical_significance' = 'high'
  GROUP BY e.id, e.name, e.description
  HAVING AVG(impact_metrics.percent_change) > 15
)
SELECT
  se.name as successful_experiment,
  r.name as candidate_region,
  r.id as region_id,
  'High potential for replication' as recommendation
FROM successful_experiments se
CROSS JOIN Region r
WHERE r.id NOT IN (
  SELECT re.region_id
  FROM RegionExperiment re
  WHERE re.experiment_id = se.id
)
  AND r.valid_to IS NULL
```

## Data Privacy

- **Storage**: EU-only (Google Cloud europe-west1)
- **PII**: None in experiment definition; participant data protected through pseudonymization
- **Access**:
  - Researchers can see experiments they are involved in
  - Region admins can see experiments in their region
  - Aggregated results are public within platform
- **GDPR**: Individual participant data anonymized; only aggregate results shared

## Validation Rules

- `status` must be one of: `planned`, `active`, `completed`, `cancelled`
- `start_date` cannot be more than 1 year in the future
- `end_date` must be after `start_date` if provided
- Cannot change status from `completed` to `active`
- Cannot change status from `cancelled` to `active`
- Must have at least one criteria via `ExperimentCriteria`
- Must have at least one participating region via `RegionExperiment`

## BigQuery Schema

```sql
CREATE TABLE experiments (
  id STRING NOT NULL,
  name STRING NOT NULL,
  description STRING NOT NULL,
  hypothesis STRING NOT NULL,
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP,
  status STRING NOT NULL,
  metadata JSON,
  _created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  _updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(start_date)
CLUSTER BY status;

-- Status constraint
ALTER TABLE experiments ADD CONSTRAINT check_experiment_status
  CHECK (status IN ('planned', 'active', 'completed', 'cancelled'));
```

## Sample Data

```json
{
  "id": "b50e8400-e29b-41d4-a716-446655440006",
  "name": "Digital Learning Pilot Q1 2024",
  "description": "Implement AI-powered adaptive learning platform for Grade 7 mathematics to improve student engagement and outcomes",
  "hypothesis": "Personalized digital content will increase student satisfaction by 20% and improve test scores by 15% within 3 months",
  "start_date": "2024-01-15T00:00:00Z",
  "end_date": "2024-04-15T00:00:00Z",
  "status": "completed",
  "metadata": {
    "intervention_type": "teaching_method",
    "budget": 50000,
    "currency": "EUR",
    "target_population": "grade_7_math_students",
    "sample_size": 450,
    "control_group": true,
    "control_group_size": 450,
    "principal_investigator": {
      "name": "Dr. Eva Horáková",
      "email": "eva.horakova@university.cz"
    },
    "resources_used": [
      "adaptive_learning_platform",
      "teacher_training_program"
    ],
    "results_summary": {
      "student_satisfaction_change": "+23%",
      "test_score_change": "+18%",
      "hypothesis_confirmed": true
    }
  }
}
```

## Experiment Types

### Teaching Methods
- Flipped classroom
- Project-based learning
- Gamification
- Adaptive learning platforms

### Professional Development
- Teacher training programs
- Peer observation systems
- Coaching and mentoring

### Curriculum Changes
- New textbook adoption
- Interdisciplinary units
- Skills-based assessment

### Technology Integration
- Learning management systems
- Digital collaboration tools
- AI tutoring assistants

### Parent Engagement
- Communication apps
- Parent workshops
- Home learning support programs
