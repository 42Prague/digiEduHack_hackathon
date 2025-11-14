# Parent

## Overview
Represents a parent or guardian involved in a student's education. Parents provide valuable feedback on school communication, student well-being, and perceived quality of education.

## Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `name` | String | Yes | Parent's full name |
| `valid_from` | DateTime | Yes | When this parent record became active |
| `valid_to` | DateTime | No | When this parent record became inactive (NULL = currently active) |
| `metadata` | JSON | No | Additional attributes (preferred language, involvement level) |

### Metadata Schema (Example)
```json
{
  "preferred_language": "cs",
  "involvement_level": "high",
  "occupation": "engineer",
  "education_level": "university",
  "communication_preferences": {
    "email": true,
    "sms": false,
    "app_notifications": true
  },
  "volunteer_roles": ["parent_council", "fundraising"]
}
```

## Methods

### `getChildren()`
Returns all students (children) associated with this parent.

**Returns:** `List<Student>`

**SQL Example:**
```sql
SELECT s.* FROM Student s
JOIN StudentParent sp ON s.id = sp.student_id
WHERE sp.parent_id = :parent_id
  AND CURRENT_TIMESTAMP BETWEEN sp.valid_from AND COALESCE(sp.valid_to, '9999-12-31')
```

## Relationships

- **Parents** many `Student` through `StudentParent` (many-to-many)
- **Provides** many `Feedback` (one-to-many)

## Temporal Behavior

Parent records track changes over time:
- **Involvement change**: Update `metadata.involvement_level`
- **Custody change**: Update `StudentParent` relationship, not parent record

Example: Update parent metadata
```sql
-- Close old record
UPDATE Parent SET valid_to = CURRENT_TIMESTAMP WHERE id = :parent_id AND valid_to IS NULL;

-- Create new record with updated metadata
INSERT INTO Parent (id, name, valid_from, metadata, ...)
VALUES (:parent_id, :name, CURRENT_TIMESTAMP, :new_metadata, ...);
```

## Use Cases

### UC1: Parent Engagement Tracking
Measure parent involvement through feedback frequency:
```sql
SELECT
  p.id,
  p.name,
  p.metadata->>'involvement_level' as involvement,
  COUNT(f.id) as feedback_count,
  AVG(f.sentiment_score) as avg_sentiment
FROM Parent p
LEFT JOIN Feedback f ON f.author_id = p.id AND f.author_type = 'parent'
WHERE f.timestamp >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY p.id, p.name, p.metadata
ORDER BY feedback_count DESC
```

### UC2: Parent-Teacher Communication
Track communication effectiveness between parents and teachers:
```sql
SELECT
  t.name as teacher,
  COUNT(DISTINCT p.id) as engaged_parents,
  AVG(f.sentiment_score) as avg_parent_satisfaction
FROM Teacher t
JOIN StudentTeacherSubject sts ON t.id = sts.teacher_id
JOIN StudentParent sp ON sts.student_id = sp.student_id
JOIN Parent p ON sp.parent_id = p.id
LEFT JOIN Feedback f ON f.author_id = p.id
  AND f.target_entity_id = t.id
  AND f.author_type = 'parent'
WHERE sts.valid_to IS NULL
GROUP BY t.id, t.name
```

### UC3: Family Support Needs
Identify families needing additional support based on feedback patterns:
```sql
SELECT
  p.id,
  p.name,
  COUNT(s.id) as num_children,
  AVG(f.sentiment_score) as avg_sentiment,
  STRING_AGG(DISTINCT f.category, ', ') as concern_areas
FROM Parent p
JOIN StudentParent sp ON p.id = sp.parent_id
JOIN Student s ON sp.student_id = s.id
LEFT JOIN Feedback f ON f.author_id = p.id
  AND f.author_type = 'parent'
  AND f.sentiment_score < -0.5
WHERE sp.valid_to IS NULL
GROUP BY p.id, p.name
HAVING AVG(f.sentiment_score) < -0.3
```

## Data Privacy

- **Storage**: EU-only (Google Cloud europe-west1)
- **PII**: CRITICAL - contains name
- **Access**:
  - Parents can only see their own data and their children's data
  - Teachers can see parents of their students (name only)
  - Region admins can see parents in their region
- **GDPR**:
  - Right to access: Export all parent data and feedback
  - Right to erasure: Set `valid_to` and redact PII in metadata
  - Right to rectification: Create new record with corrected data
- **Note**: Contact information (email, phone) should be managed in a separate Contact Management System

## Validation Rules

- `name` must not be empty
- Cannot have overlapping active records (only one record with `valid_to IS NULL`)
- Must have at least one active child relationship via `StudentParent`
- Cannot delete parent if active feedback exists

## BigQuery Schema

```sql
CREATE TABLE parents (
  id STRING NOT NULL,
  name STRING NOT NULL,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  metadata JSON,
  _created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  _updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(valid_from)
CLUSTER BY id;

-- PII protection
CREATE ROW ACCESS POLICY parent_privacy ON parents
GRANT TO ('teacher@project.iam.gserviceaccount.com')
FILTER USING (
  id IN (
    SELECT sp.parent_id FROM StudentParent sp
    JOIN StudentTeacherSubject sts ON sp.student_id = sts.student_id
    WHERE sts.teacher_id = SESSION_USER()
  )
);
```

## Sample Data (Development Only)

```json
{
  "id": "650e8400-e29b-41d4-a716-446655440001",
  "name": "Marie Nováková",
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_to": null,
  "metadata": {
    "preferred_language": "cs",
    "involvement_level": "high",
    "occupation": "engineer",
    "education_level": "university",
    "communication_preferences": {
      "email": true,
      "sms": false,
      "app_notifications": true
    },
    "volunteer_roles": ["parent_council"]
  }
}
```

**Note**: Contact details (email, phone) are managed in a separate Contact Management System and linked via `parent_id`.

## Parent Feedback Categories

Common categories for parent feedback:
- `communication` - School-parent communication quality
- `safety` - School safety and security concerns
- `curriculum` - Curriculum quality and relevance
- `facilities` - School facilities and resources
- `teacher_quality` - Teacher professionalism and effectiveness
- `student_wellbeing` - Child's emotional and social well-being
- `academic_progress` - Child's academic development
- `extracurricular` - After-school activities and programs
