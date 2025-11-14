# Student

## Overview
Represents a learner enrolled in the education system. Students are the primary beneficiaries of educational interventions and key sources of feedback on teaching quality and learning outcomes.

## Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `name` | String | Yes | Student's full name (pseudonymized in production) |
| `birth_date` | Date | Yes | Date of birth for age-based analysis |
| `current_region_id` | UUID | Yes | Current region where student is enrolled |
| `current_school_id` | UUID | Yes | Current school identifier |
| `valid_from` | DateTime | Yes | When this student record became active |
| `valid_to` | DateTime | No | When this student record became inactive (NULL = currently active) |
| `metadata` | JSON | No | Additional attributes (grade level, special needs, etc.) |

### Metadata Schema (Example)
```json
{
  "grade_level": 8,
  "enrollment_date": "2023-09-01",
  "special_needs": false,
  "language_preference": "cs",
  "previous_schools": [
    {
      "school_id": "uuid-previous-school",
      "from": "2020-09-01",
      "to": "2023-06-30"
    }
  ],
  "pseudonym": "Student_A7X3K"
}
```

## Methods

### `getHistory()`
Returns complete history of student's school and region changes.

**Returns:** `List<StudentRecord>`

**SQL Example:**
```sql
SELECT * FROM Student
WHERE id = :student_id
ORDER BY valid_from DESC
```

### `getCurrentTeachers()`
Returns all teachers currently teaching this student.

**Returns:** `List<Teacher>`

**SQL Example:**
```sql
SELECT DISTINCT t.* FROM Teacher t
JOIN StudentTeacherSubject sts ON t.id = sts.teacher_id
WHERE sts.student_id = :student_id
  AND CURRENT_TIMESTAMP BETWEEN sts.valid_from AND COALESCE(sts.valid_to, '9999-12-31')
```

## Relationships

- **Belongs to** one `Region` (many-to-one)
- **Has** many `Parent` through `StudentParent` (many-to-many)
- **Enrolled in** many `Subject` through `StudentTeacherSubject` (many-to-many)
- **Taught by** many `Teacher` through `StudentTeacherSubject` (many-to-many)
- **Provides** many `Feedback` (one-to-many)

## Temporal Behavior

Students track changes over time:
- **School transfer**: Create new record with updated `current_school_id` and `valid_from = transfer_date`
- **Region move**: Create new record with updated `current_region_id`
- **Grade progression**: Update `metadata.grade_level` annually

Example: Student transfers from School A to School B
```sql
-- Close old record
UPDATE Student SET valid_to = '2024-06-30' WHERE id = :student_id AND valid_to IS NULL;

-- Create new record
INSERT INTO Student (id, name, current_school_id, valid_from, ...)
VALUES (:student_id, :name, :new_school_id, '2024-09-01', ...);
```

## Use Cases

### UC1: Student Progress Tracking
Track a student's performance across subjects over time:
```sql
SELECT
  sub.name as subject,
  AVG(f.sentiment_score) as avg_feedback,
  COUNT(f.id) as feedback_count
FROM Student s
JOIN StudentTeacherSubject sts ON s.id = sts.student_id
JOIN Subject sub ON sts.subject_id = sub.id
LEFT JOIN Feedback f ON f.author_id = s.id AND f.author_type = 'student'
WHERE s.id = :student_id
  AND f.timestamp BETWEEN :start_date AND :end_date
GROUP BY sub.name
```

### UC2: Cohort Analysis
Compare students who started in the same period:
```sql
SELECT
  s.current_region_id,
  AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, s.birth_date))) as avg_age,
  COUNT(DISTINCT s.id) as student_count
FROM Student s
WHERE s.metadata->>'enrollment_date' BETWEEN '2023-09-01' AND '2024-08-31'
  AND s.valid_to IS NULL
GROUP BY s.current_region_id
```

### UC3: Student Feedback Impact
Measure how student feedback correlates with teacher changes:
```sql
SELECT
  t.id,
  AVG(f.sentiment_score) as avg_student_feedback
FROM Teacher t
JOIN StudentTeacherSubject sts ON t.id = sts.teacher_id
JOIN Feedback f ON f.author_id = sts.student_id
  AND f.author_type = 'student'
  AND f.target_entity_id = t.id
WHERE f.timestamp BETWEEN sts.valid_from AND COALESCE(sts.valid_to, CURRENT_TIMESTAMP)
GROUP BY t.id
HAVING AVG(f.sentiment_score) < -0.3
```

## Data Privacy

- **Storage**: EU-only (Google Cloud europe-west1)
- **PII**: CRITICAL - contains birth_date and name
- **Pseudonymization**: Production systems MUST use pseudonyms in `metadata.pseudonym`
- **Access**:
  - Teachers can only see their own students
  - Region admins can see students in their region
  - Parents can only see their own children
- **GDPR**: Right to erasure - set `valid_to` and mark as deleted in metadata

## Validation Rules

- `birth_date` must result in age between 5 and 19 years
- `current_region_id` must reference existing active Region
- `current_school_id` must exist in region's school list
- Cannot have overlapping active records (only one record with `valid_to IS NULL`)
- New records must have `valid_from > previous_record.valid_from`

## BigQuery Schema

```sql
CREATE TABLE students (
  id STRING NOT NULL,
  name STRING NOT NULL,
  birth_date DATE NOT NULL,
  current_region_id STRING NOT NULL,
  current_school_id STRING NOT NULL,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  metadata JSON,
  _created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  _updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(valid_from)
CLUSTER BY current_region_id, current_school_id;

-- Enforce pseudonymization in production
CREATE ROW ACCESS POLICY student_privacy ON students
GRANT TO ('data-analyst@project.iam.gserviceaccount.com')
FILTER USING (metadata->>'pseudonym' IS NOT NULL);
```

## Sample Data (Development Only)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Jan Novák",
  "birth_date": "2012-05-15",
  "current_region_id": "region-prague-5",
  "current_school_id": "school-zs-barrandov",
  "valid_from": "2024-09-01T00:00:00Z",
  "valid_to": null,
  "metadata": {
    "grade_level": 7,
    "enrollment_date": "2019-09-01",
    "special_needs": false,
    "language_preference": "cs",
    "pseudonym": "Student_X5K2P"
  }
}
```
