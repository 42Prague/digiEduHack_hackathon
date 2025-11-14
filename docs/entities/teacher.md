# Teacher

## Overview
Represents an educator teaching subjects to students. Teachers are key stakeholders providing feedback on curriculum effectiveness, student engagement, and implementation challenges.

## Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `name` | String | Yes | Teacher's full name |
| `current_region_id` | UUID | Yes | Current region where teacher works |
| `current_school_id` | UUID | Yes | Current school identifier |
| `qualifications` | List\<String\> | No | List of teaching certifications and degrees |
| `valid_from` | DateTime | Yes | When this teacher record became active |
| `valid_to` | DateTime | No | When this teacher record became inactive (NULL = currently active) |
| `metadata` | JSON | No | Additional attributes (specializations, experience) |

### Metadata Schema (Example)
```json
{
  "years_experience": 8,
  "specializations": ["mathematics", "physics"],
  "certifications": [
    {
      "name": "Advanced Mathematics Teaching Certificate",
      "issued_by": "Ministry of Education",
      "issued_date": "2020-06-15",
      "expiry_date": "2025-06-15"
    }
  ],
  "employment_type": "full_time",
  "weekly_hours": 40,
  "subjects_taught": ["math_grade_7", "math_grade_8", "physics_grade_9"],
  "professional_development": [
    {
      "course": "Digital Teaching Methods",
      "completed": "2023-11-20",
      "hours": 40
    }
  ]
}
```

## Methods

### `getHistory()`
Returns complete history of teacher's school and region changes.

**Returns:** `List<TeacherRecord>`

**SQL Example:**
```sql
SELECT * FROM Teacher
WHERE id = :teacher_id
ORDER BY valid_from DESC
```

### `getCurrentSubjects()`
Returns all subjects currently taught by this teacher.

**Returns:** `List<Subject>`

**SQL Example:**
```sql
SELECT DISTINCT sub.* FROM Subject sub
JOIN StudentTeacherSubject sts ON sub.id = sts.subject_id
WHERE sts.teacher_id = :teacher_id
  AND CURRENT_TIMESTAMP BETWEEN sts.valid_from AND COALESCE(sts.valid_to, '9999-12-31')
```

## Relationships

- **Belongs to** one `Region` (many-to-one)
- **Teaches** many `Subject` through `StudentTeacherSubject` (many-to-many)
- **Teaches** many `Student` through `StudentTeacherSubject` (many-to-many)
- **Provides** many `Feedback` (one-to-many)

## Temporal Behavior

Teachers track employment and assignment changes:
- **School transfer**: Create new record with updated `current_school_id` and `valid_from`
- **Region relocation**: Create new record with updated `current_region_id`
- **Subject assignment change**: Update `StudentTeacherSubject` relationships
- **Qualification update**: Add to `qualifications` list in new record

Example: Teacher transfers to new school
```sql
-- Close old record
UPDATE Teacher SET valid_to = '2024-08-31' WHERE id = :teacher_id AND valid_to IS NULL;

-- Create new record
INSERT INTO Teacher (id, name, current_school_id, current_region_id, valid_from, ...)
VALUES (:teacher_id, :name, :new_school_id, :new_region_id, '2024-09-01', ...);

-- Update teaching assignments
UPDATE StudentTeacherSubject SET valid_to = '2024-08-31'
WHERE teacher_id = :teacher_id AND valid_to IS NULL;
```

## Use Cases

### UC1: Teacher Workload Analysis
Calculate teaching load and student count per teacher:
```sql
SELECT
  t.id,
  t.name,
  COUNT(DISTINCT sts.subject_id) as subjects_taught,
  COUNT(DISTINCT sts.student_id) as total_students,
  t.metadata->>'weekly_hours' as hours_per_week
FROM Teacher t
JOIN StudentTeacherSubject sts ON t.id = sts.teacher_id
WHERE sts.valid_to IS NULL
  AND t.valid_to IS NULL
GROUP BY t.id, t.name, t.metadata
ORDER BY total_students DESC
```

### UC2: Teacher Effectiveness Tracking
Measure teacher effectiveness through student feedback:
```sql
SELECT
  t.id,
  t.name,
  sub.name as subject,
  AVG(f.sentiment_score) as avg_student_feedback,
  COUNT(f.id) as feedback_count
FROM Teacher t
JOIN StudentTeacherSubject sts ON t.id = sts.teacher_id
JOIN Subject sub ON sts.subject_id = sub.id
JOIN Feedback f ON f.target_entity_id = t.id
  AND f.author_type = 'student'
  AND f.target_entity_type = 'teacher'
WHERE f.timestamp >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY t.id, t.name, sub.name
HAVING COUNT(f.id) >= 5
ORDER BY avg_student_feedback DESC
```

### UC3: Professional Development Impact
Correlate teacher training with student outcomes:
```sql
WITH teacher_training AS (
  SELECT
    id,
    name,
    JSONB_ARRAY_LENGTH(metadata->'professional_development') as training_count
  FROM Teacher
  WHERE valid_to IS NULL
)
SELECT
  tt.training_count,
  AVG(f.sentiment_score) as avg_effectiveness
FROM teacher_training tt
JOIN Feedback f ON f.target_entity_id = tt.id
  AND f.target_entity_type = 'teacher'
WHERE f.timestamp >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY tt.training_count
ORDER BY tt.training_count
```

### UC4: Teacher Retention Analysis
Track teacher turnover rates by region:
```sql
SELECT
  r.name as region,
  COUNT(DISTINCT t.id) as total_teachers,
  COUNT(DISTINCT CASE WHEN t.valid_to IS NOT NULL THEN t.id END) as departed_teachers,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN t.valid_to IS NOT NULL THEN t.id END) /
        NULLIF(COUNT(DISTINCT t.id), 0), 2) as turnover_rate
FROM Teacher t
JOIN Region r ON t.current_region_id = r.id
WHERE t.valid_from >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY r.name
ORDER BY turnover_rate DESC
```

## Data Privacy

- **Storage**: EU-only (Google Cloud europe-west1)
- **PII**: Contains name and employment history
- **Access**:
  - Teachers can see their own data
  - School admins can see teachers in their school
  - Region admins can see teachers in their region
  - Students/parents can see name and qualifications only
- **GDPR**: Right to erasure - set `valid_to` and anonymize in metadata

## Validation Rules

- `current_region_id` must reference existing active Region
- `current_school_id` must exist in region's school list
- `qualifications` must contain valid certification codes
- Cannot have overlapping active records (only one record with `valid_to IS NULL`)
- New records must have `valid_from > previous_record.valid_from`
- Must have at least one active teaching assignment via `StudentTeacherSubject`

## BigQuery Schema

```sql
CREATE TABLE teachers (
  id STRING NOT NULL,
  name STRING NOT NULL,
  current_region_id STRING NOT NULL,
  current_school_id STRING NOT NULL,
  qualifications ARRAY<STRING>,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  metadata JSON,
  _created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  _updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(valid_from)
CLUSTER BY current_region_id, current_school_id;

-- Index for performance
CREATE INDEX idx_teacher_active ON teachers(id, valid_to) WHERE valid_to IS NULL;
```

## Sample Data (Development Only)

```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "name": "Petra Svobodová",
  "current_region_id": "region-prague-5",
  "current_school_id": "school-zs-barrandov",
  "qualifications": [
    "CERT_MATH_SECONDARY",
    "CERT_PHYSICS_SECONDARY"
  ],
  "valid_from": "2024-09-01T00:00:00Z",
  "valid_to": null,
  "metadata": {
    "years_experience": 8,
    "specializations": ["mathematics", "physics"],
    "employment_type": "full_time",
    "weekly_hours": 40,
    "subjects_taught": ["math_grade_7", "math_grade_8"],
    "professional_development": [
      {
        "course": "Digital Teaching Methods",
        "completed": "2023-11-20",
        "hours": 40
      }
    ]
  }
}
```

## Teacher Feedback Categories

Common categories for teacher feedback:
- `curriculum_clarity` - Clarity of curriculum guidelines
- `resource_availability` - Availability of teaching materials
- `student_engagement` - Student participation and motivation
- `administrative_burden` - Administrative workload
- `professional_support` - Support from school leadership
- `technology_tools` - Quality of digital teaching tools
- `training_needs` - Areas needing professional development
- `classroom_management` - Classroom discipline and management
