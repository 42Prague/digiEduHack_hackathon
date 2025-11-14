# Subject

## Overview
Represents an academic discipline or topic taught in the education system. Subjects form the core of the teaching-learning relationship and serve as a context for performance measurement.

## Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `name` | String | Yes | Subject name (e.g., "Mathematics", "Physics") |
| `category` | String | Yes | Subject category (e.g., "STEM", "Languages", "Arts") |
| `level` | String | Yes | Education level (e.g., "primary", "secondary") |
| `metadata` | JSON | No | Additional attributes (curriculum standards, prerequisites) |

### Metadata Schema (Example)
```json
{
  "curriculum_code": "MAT-SEC-7",
  "description": "Secondary Mathematics Grade 7",
  "prerequisites": ["MAT-PRI-6"],
  "weekly_hours": 4,
  "assessment_type": "continuous",
  "learning_outcomes": [
    "Solve linear equations",
    "Understand basic geometry",
    "Apply statistics fundamentals"
  ],
  "topics": [
    "Algebra",
    "Geometry",
    "Statistics"
  ]
}
```

## Methods

### `getTeachers()`
Returns all teachers currently teaching this subject.

**Returns:** `List<Teacher>`

**SQL Example:**
```sql
SELECT DISTINCT t.* FROM Teacher t
JOIN StudentTeacherSubject sts ON t.id = sts.teacher_id
WHERE sts.subject_id = :subject_id
  AND CURRENT_TIMESTAMP BETWEEN sts.valid_from AND COALESCE(sts.valid_to, '9999-12-31')
```

### `getStudents()`
Returns all students currently enrolled in this subject.

**Returns:** `List<Student>`

**SQL Example:**
```sql
SELECT DISTINCT s.* FROM Student s
JOIN StudentTeacherSubject sts ON s.id = sts.student_id
WHERE sts.subject_id = :subject_id
  AND CURRENT_TIMESTAMP BETWEEN sts.valid_from AND COALESCE(sts.valid_to, '9999-12-31')
```

## Relationships

- **Taught in** many `StudentTeacherSubject` (one-to-many)
- **Taught by** many `Teacher` through `StudentTeacherSubject` (many-to-many)
- **Learned by** many `Student` through `StudentTeacherSubject` (many-to-many)

## Use Cases

### UC1: Subject Performance Analysis
Analyze performance across all regions for a specific subject:
```sql
SELECT
  r.name as region,
  COUNT(DISTINCT sts.student_id) as enrolled_students,
  AVG(f.sentiment_score) as avg_student_satisfaction
FROM Subject sub
JOIN StudentTeacherSubject sts ON sub.id = sts.subject_id
JOIN Region r ON sts.region_id = r.id
LEFT JOIN Feedback f ON f.author_type = 'student'
  AND f.target_entity_type = 'subject'
  AND f.target_entity_id = sub.id
WHERE sub.name = :subject_name
  AND sts.valid_to IS NULL
GROUP BY r.name
ORDER BY avg_student_satisfaction DESC
```

### UC2: Subject Difficulty Assessment
Identify subjects with lowest student satisfaction:
```sql
SELECT
  sub.name,
  sub.level,
  COUNT(f.id) as feedback_count,
  AVG(f.sentiment_score) as avg_sentiment
FROM Subject sub
LEFT JOIN Feedback f ON f.target_entity_id = sub.id
  AND f.target_entity_type = 'subject'
  AND f.author_type = 'student'
WHERE f.timestamp >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY sub.id, sub.name, sub.level
HAVING COUNT(f.id) >= 10
ORDER BY avg_sentiment ASC
LIMIT 10
```

### UC3: Teacher-Subject Matching
Find most effective teacher-subject pairings:
```sql
SELECT
  t.name as teacher,
  sub.name as subject,
  COUNT(DISTINCT sts.student_id) as students_taught,
  AVG(f.sentiment_score) as effectiveness
FROM Teacher t
JOIN StudentTeacherSubject sts ON t.id = sts.teacher_id
JOIN Subject sub ON sts.subject_id = sub.id
LEFT JOIN Feedback f ON f.target_entity_id = t.id
  AND f.author_type = 'student'
WHERE sts.valid_to IS NULL
GROUP BY t.name, sub.name
HAVING COUNT(DISTINCT sts.student_id) >= 20
ORDER BY effectiveness DESC
```

## Data Privacy

- **Storage**: EU-only (Google Cloud europe-west1)
- **PII**: None - subjects are non-personal data
- **Access**: Public within the education system
- **GDPR**: Not applicable (no personal data)

## Validation Rules

- `name` must be unique within same `category` and `level`
- `category` must be one of predefined values (STEM, Languages, Arts, Social_Sciences, etc.)
- `level` must be one of: `primary`, `secondary`, `vocational`
- `metadata.curriculum_code` should follow regional standards

## BigQuery Schema

```sql
CREATE TABLE subjects (
  id STRING NOT NULL,
  name STRING NOT NULL,
  category STRING NOT NULL,
  level STRING NOT NULL,
  metadata JSON,
  _created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  _updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY category, level;

-- Unique constraint
CREATE UNIQUE INDEX idx_subject_unique ON subjects(name, category, level);
```

## Sample Data

```json
{
  "id": "850e8400-e29b-41d4-a716-446655440003",
  "name": "Mathematics",
  "category": "STEM",
  "level": "secondary",
  "metadata": {
    "curriculum_code": "MAT-SEC-7",
    "description": "Secondary Mathematics Grade 7",
    "weekly_hours": 4,
    "assessment_type": "continuous",
    "learning_outcomes": [
      "Solve linear equations",
      "Understand basic geometry",
      "Apply statistics fundamentals"
    ],
    "topics": [
      "Algebra",
      "Geometry",
      "Statistics"
    ]
  }
}
```

## Standard Subject Categories

- **STEM**: Mathematics, Physics, Chemistry, Biology, Computer Science
- **Languages**: Native Language, Foreign Languages, Literature
- **Arts**: Music, Visual Arts, Drama, Design
- **Social_Sciences**: History, Geography, Civics, Economics
- **Physical_Education**: Sports, Health Education
- **Vocational**: Technical Skills, Professional Training
