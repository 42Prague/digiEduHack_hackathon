# Rule

## Overview
Represents a normative document or requirement that must be fulfilled in a region. Rules can originate from government regulations, school policies, or requirements imposed by EduZmena platform.

## Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `title` | String | Yes | Short descriptive title |
| `description` | String | Yes | Detailed description of the rule |
| `type` | String | Yes | Rule origin: `government`, `school`, `eduzmena` |
| `source_url` | String | No | Link to official document or regulation |
| `effective_from` | DateTime | Yes | When rule becomes active |
| `effective_to` | DateTime | No | When rule expires (NULL = no expiration) |
| `requirements` | JSON | Yes | Structured requirements definition |

### Requirements Schema (Example)
```json
{
  "compliance_level": "mandatory",
  "applies_to": ["teachers", "students", "schools"],
  "verification_method": "quarterly_audit",
  "penalties": {
    "non_compliance": "warning_first_then_suspension"
  },
  "requirements_list": [
    {
      "id": "req-1",
      "description": "Minimum 180 teaching days per year",
      "measurable": true,
      "metric": "teaching_days_count",
      "threshold": 180
    },
    {
      "id": "req-2",
      "description": "Teacher-student ratio not exceeding 1:25",
      "measurable": true,
      "metric": "teacher_student_ratio",
      "threshold": 25
    }
  ]
}
```

## Methods

### `isActiveAt(DateTime timestamp)`
Checks if rule is active at given timestamp.

**Returns:** `Boolean`

**Logic:**
```python
def isActiveAt(self, timestamp):
    return (self.effective_from <= timestamp and
            (self.effective_to is None or timestamp <= self.effective_to))
```

## Relationships

- **Applied in** many `Region` through `RegionRule` (many-to-many)
- **Referenced by** many `Feedback` (implicit - feedback can mention rule compliance)

## Temporal Behavior

Rules have temporal validity:
- **New rule**: Create with `effective_from` in future for planned regulations
- **Rule amendment**: Create new rule record, set old rule's `effective_to`
- **Rule expiration**: Set `effective_to` to mark when rule is no longer applicable

Example: Government updates minimum teaching hours requirement
```sql
-- Expire old rule
UPDATE Rule SET effective_to = '2024-12-31'
WHERE id = 'old-rule-uuid';

-- Create new rule
INSERT INTO Rule (id, title, description, type, effective_from, requirements)
VALUES (
  'new-rule-uuid',
  'Updated Minimum Teaching Hours 2025',
  'New regulation effective 2025',
  'government',
  '2025-01-01',
  '{"requirements_list": [...]}'::json
);
```

## Use Cases

### UC1: Rule Compliance Monitoring
Check which regions are compliant with specific rule:
```sql
SELECT
  r.name as region,
  ru.title as rule,
  rr.status,
  CASE
    WHEN rr.status = 'active' AND ru.isActiveAt(CURRENT_TIMESTAMP) THEN 'Compliant'
    ELSE 'Non-Compliant'
  END as compliance_status
FROM Region r
JOIN RegionRule rr ON r.id = rr.region_id
JOIN Rule ru ON rr.rule_id = ru.id
WHERE ru.type = 'government'
  AND ru.effective_from <= CURRENT_TIMESTAMP
  AND (ru.effective_to IS NULL OR ru.effective_to >= CURRENT_TIMESTAMP)
```

### UC2: Rule Impact Analysis
Measure how rule introduction affects feedback sentiment:
```sql
WITH rule_adoption AS (
  SELECT
    rr.region_id,
    ru.id as rule_id,
    ru.title,
    rr.adopted_from
  FROM RegionRule rr
  JOIN Rule ru ON rr.rule_id = ru.id
  WHERE ru.id = :specific_rule_id
)
SELECT
  ra.title,
  AVG(CASE WHEN f.timestamp < ra.adopted_from THEN f.sentiment_score END) as sentiment_before,
  AVG(CASE WHEN f.timestamp >= ra.adopted_from THEN f.sentiment_score END) as sentiment_after,
  AVG(CASE WHEN f.timestamp >= ra.adopted_from THEN f.sentiment_score END) -
  AVG(CASE WHEN f.timestamp < ra.adopted_from THEN f.sentiment_score END) as sentiment_change
FROM rule_adoption ra
JOIN Feedback f ON f.target_entity_type = 'region' AND f.target_entity_id = ra.region_id
WHERE f.timestamp BETWEEN ra.adopted_from - INTERVAL '3 months'
                      AND ra.adopted_from + INTERVAL '3 months'
GROUP BY ra.title
```

### UC3: Rule Coverage Gap Analysis
Identify regions not complying with mandatory rules:
```sql
SELECT
  r.id,
  r.name,
  ru.title as missing_rule
FROM Region r
CROSS JOIN Rule ru
LEFT JOIN RegionRule rr ON r.id = rr.region_id AND ru.id = rr.rule_id
WHERE ru.type = 'government'
  AND ru.requirements->>'compliance_level' = 'mandatory'
  AND ru.effective_from <= CURRENT_TIMESTAMP
  AND (ru.effective_to IS NULL OR ru.effective_to >= CURRENT_TIMESTAMP)
  AND (rr.region_id IS NULL OR rr.status != 'active')
  AND r.valid_to IS NULL
```

## Data Privacy

- **Storage**: EU-only (Google Cloud europe-west1)
- **PII**: None - rules are public policy documents
- **Access**: Public within the education system
- **GDPR**: Not applicable (no personal data)

## Validation Rules

- `type` must be one of: `government`, `school`, `eduzmena`
- `effective_from` cannot be more than 2 years in the future
- `effective_to` must be after `effective_from`
- `requirements` must conform to JSON schema
- `source_url` must be valid URL if provided
- Cannot delete rule if referenced in active `RegionRule`

## BigQuery Schema

```sql
CREATE TABLE rules (
  id STRING NOT NULL,
  title STRING NOT NULL,
  description STRING NOT NULL,
  type STRING NOT NULL,
  source_url STRING,
  effective_from TIMESTAMP NOT NULL,
  effective_to TIMESTAMP,
  requirements JSON NOT NULL,
  _created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  _updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(effective_from)
CLUSTER BY type;

-- Check constraint
ALTER TABLE rules ADD CONSTRAINT check_rule_type
  CHECK (type IN ('government', 'school', 'eduzmena'));
```

## Sample Data

```json
{
  "id": "950e8400-e29b-41d4-a716-446655440004",
  "title": "Minimum Teaching Standards 2024",
  "description": "National regulation defining minimum requirements for teaching quality and school operations",
  "type": "government",
  "source_url": "https://www.msmt.cz/regulations/teaching-standards-2024",
  "effective_from": "2024-01-01T00:00:00Z",
  "effective_to": null,
  "requirements": {
    "compliance_level": "mandatory",
    "applies_to": ["teachers", "schools"],
    "verification_method": "annual_inspection",
    "penalties": {
      "non_compliance": "warning_then_funding_reduction"
    },
    "requirements_list": [
      {
        "id": "req-1",
        "description": "Minimum 180 teaching days per year",
        "measurable": true,
        "metric": "teaching_days_count",
        "threshold": 180
      },
      {
        "id": "req-2",
        "description": "Teacher qualification certificate required",
        "measurable": true,
        "metric": "teacher_certification_rate",
        "threshold": 100
      }
    ]
  }
}
```

## Rule Types

### Government Rules
- National curriculum standards
- Teacher qualification requirements
- Minimum teaching hours
- Student assessment regulations
- School safety requirements

### School Rules
- Attendance policies
- Grading systems
- Behavioral codes
- Uniform requirements
- Extracurricular participation

### EduZmena Rules
- Data reporting requirements
- Feedback submission frequency
- Platform usage standards
- Data quality thresholds
- Experiment participation criteria
