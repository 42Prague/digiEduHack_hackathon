# Region

## Overview
Central organizational unit representing ANY organizational or administrative boundary in the education system. **Important**: A region can represent any level of organization - a single school, a district, a city, a county, or any other grouping. There is no separate "school" entity - schools are represented as regions with appropriate `type` classification.

Regions group students and teachers, define applicable rules, track specific criteria, and participate in experiments.

## Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `name` | String | Yes | Human-readable region name (e.g., "Prague District 5", "Elementary School Palmovka") |
| `country` | String | Yes | ISO 3166-1 alpha-2 country code (e.g., "CZ") |
| `type` | String | Yes | Classification of organizational level and context. Examples: `school`, `school_urban`, `school_rural`, `district`, `city`, `county`, `region`, `country` |
| `metadata` | JSON | No | Flexible storage for region-specific attributes (can include organizational_level, parent_region_id, etc.) |

### Metadata Schema (Examples)

**Example 1: District-level region**
```json
{
  "organizational_level": "district",
  "population": 45000,
  "schools_count": 12,
  "timezone": "Europe/Prague",
  "language": "cs",
  "economic_index": "medium",
  "join_date": "2024-01-15",
  "contact_person": {
    "name": "Jana Nováková",
    "email": "jana.novakova@region.cz"
  }
}
```

**Example 2: School-level region**
```json
{
  "organizational_level": "school",
  "parent_region_id": "uuid-of-district",
  "school_type": "elementary",
  "students_capacity": 500,
  "address": "Palmovka 123, Prague 8",
  "timezone": "Europe/Prague",
  "language": "cs",
  "join_date": "2024-01-15",
  "principal": {
    "name": "Petr Svoboda",
    "email": "principal@school-palmovka.cz"
  }
}
```

## Methods

### `getActiveRules()`
Returns all rules currently applicable to this region.

**Returns:** `List<Rule>`

**SQL Example:**
```sql
SELECT r.* FROM Rule r
JOIN RegionRule rr ON r.id = rr.rule_id
WHERE rr.region_id = :region_id
  AND rr.status = 'active'
  AND CURRENT_TIMESTAMP BETWEEN rr.adopted_from AND COALESCE(rr.adopted_to, '9999-12-31')
```

### `getActiveCriteria()`
Returns all criteria currently being tracked in this region.

**Returns:** `List<Criteria>`

### `getActiveExperiments()`
Returns all experiments currently running in this region.

**Returns:** `List<Experiment>`

## Relationships

- **Has** many `Student` (one-to-many via current_region_id)
- **Employs** many `Teacher` (one-to-many via current_region_id)
- **Tracks student history** through `StudentRegionHistory` (one-to-many) - tracks when students were enrolled in this region
- **Tracks teacher history** through `TeacherRegionHistory` (one-to-many) - tracks when teachers worked in this region
- **Follows** many `Rule` through `RegionRule` (many-to-many)
- **Tracks** many `Criteria` through `RegionCriteria` (many-to-many)
- **Participates in** many `Experiment` through `RegionExperiment` (many-to-many)

## Notes

- Region entity does NOT have temporal fields (`valid_from`/`valid_to`) - regions are considered permanent entities
- Temporal tracking of student/teacher relationships with regions is done via `StudentRegionHistory` and `TeacherRegionHistory` junction tables
- Region metadata changes should be tracked via audit logs or metadata versioning if needed

## Use Cases

### UC1: Region Onboarding
When a new region (school/district/etc.) joins the system:
1. Create Region record with `metadata.join_date = NOW()`
2. Capture baseline metrics via `RegionCriteria` with `baseline_value`
3. Assign applicable national rules via `RegionRule`

### UC2: Cross-Regional Comparison
Compare Region A (6 months old) with Region B (2 years old) at same lifecycle stage:
```sql
SELECT
  r.name,
  AVG(f.sentiment_score) as avg_sentiment,
  CAST(JSON_EXTRACT_SCALAR(r.metadata, '$.join_date') AS DATE) as join_date
FROM Region r
JOIN Feedback f ON f.target_entity_type = 'region' AND f.target_entity_id = r.id
WHERE f.timestamp BETWEEN
  CAST(JSON_EXTRACT_SCALAR(r.metadata, '$.join_date') AS TIMESTAMP)
  AND TIMESTAMP_ADD(CAST(JSON_EXTRACT_SCALAR(r.metadata, '$.join_date') AS TIMESTAMP), INTERVAL 6 MONTH)
GROUP BY r.name, join_date
```

### UC3: Network-Wide Aggregation
Calculate average performance across all active regions:
```sql
SELECT AVG(baseline_value) as network_average
FROM RegionCriteria rc
JOIN Region r ON rc.region_id = r.id
WHERE rc.criteria_id = :specific_criteria_id
  AND rc.valid_to IS NULL
```

## Data Privacy

- **Storage**: EU-only (Google Cloud europe-west1)
- **PII**: Minimal - only region name and contact email in metadata
- **Access**: Region administrators can only see their own region data
- **Audit**: All changes logged with timestamps

## Validation Rules

- `name` must be unique within same country and organizational level
- `type` can be any string describing the organizational level/context (e.g., `school`, `district`, `city`, `school_urban`, etc.)
- Cannot delete region if active students/teachers exist
- If `metadata.parent_region_id` is set, the parent region must exist

## BigQuery Schema

```sql
CREATE TABLE regions (
  id STRING NOT NULL,
  name STRING NOT NULL,
  country STRING NOT NULL,
  type STRING NOT NULL,
  metadata JSON,
  _created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  _updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY country, type;
```

**Note**: Temporal tracking is handled by `student_region_history` and `teacher_region_history` tables, not by the region table itself.
