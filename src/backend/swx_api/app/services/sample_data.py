from __future__ import annotations

from datetime import datetime
from typing import Dict, List


SAMPLE_DATASETS = [
    {
        "name": "praha_insight",
        "description": "Aggregated indicators for Prague pilot schools (synthetic)",
        "metrics": {
            "teacher_satisfaction": {
                "mean": 4.2,
                "median": 4.1,
                "std": 0.35,
                "min": 3.7,
                "max": 4.8,
            },
            "math_growth_index": {
                "mean": 12.4,
                "median": 11.8,
                "std": 3.2,
                "min": 7.9,
                "max": 19.6,
            },
        },
        "regions": [
            {"region": "Praha 1", "teacher_satisfaction": 4.4},
            {"region": "Praha 5", "teacher_satisfaction": 4.0},
            {"region": "Praha 9", "teacher_satisfaction": 4.1},
        ],
        "themes": [
            "Mentoring networks drive faster onboarding of new teachers.",
            "Schools need lightweight analytics dashboards to monitor interventions.",
            "Cross-regional sharing accelerates adoption of successful programmes.",
        ],
    }
]

SAMPLE_SCHOOLS = [
    {
        "dataset": "praha_insight",
        "name": "ZŠ Vltava",
        "region": "Praha 5",
        "attributes": {
            "teacher_satisfaction": 4.1,
            "math_growth_index": 11.9,
            "students": 420,
        },
    },
    {
        "dataset": "praha_insight",
        "name": "Gymnázium Karlín",
        "region": "Praha 8",
        "attributes": {
            "teacher_satisfaction": 4.5,
            "math_growth_index": 18.2,
            "students": 610,
        },
    },
    {
        "dataset": "praha_insight",
        "name": "ZŠ Anděl",
        "region": "Praha 5",
        "attributes": {
            "teacher_satisfaction": 3.9,
            "math_growth_index": 9.7,
            "students": 390,
        },
    },
]


def _timestamp() -> str:
    return datetime.utcnow().isoformat()


def get_sample_metrics() -> Dict[str, object]:
    dataset = SAMPLE_DATASETS[0]
    return {
        "datasets": [dataset["name"]],
        "metrics": dataset["metrics"],
        "generated_at": _timestamp(),
    }


def get_sample_trend(metric: str) -> Dict[str, object]:
    dataset = SAMPLE_DATASETS[0]
    field = metric if metric in dataset["metrics"] else "teacher_satisfaction"
    results: List[Dict[str, object]] = []
    for region_entry in dataset["regions"]:
        value = region_entry.get(field) or region_entry.get("teacher_satisfaction")
        if value is None:
            continue
        results.append(
            {
                "region": region_entry["region"],
                "mean": float(value),
                "median": float(value),
                "count": 12,
            }
        )
    return {
        "metric": field,
        "results": results,
        "generated_at": _timestamp(),
        "sample": True,
    }


def get_sample_themes() -> List[Dict[str, object]]:
    dataset = SAMPLE_DATASETS[0]
    return [
        {
            "dataset": dataset["name"],
            "themes": dataset["themes"],
            "generated_at": _timestamp(),
            "sample": True,
        }
    ]


def search_sample_schools(query: str) -> List[Dict[str, object]]:
    query_lower = query.lower()
    return [
        school
        for school in SAMPLE_SCHOOLS
        if query_lower in school["name"].lower() or query_lower in (school["region"] or "").lower()
    ]


def compare_sample_schools(names: List[str]) -> Dict[str, Dict[str, float]]:
    name_set = {name.lower() for name in names}
    comparison = {}
    for school in SAMPLE_SCHOOLS:
        if school["name"].lower() in name_set:
            comparison[school["name"]] = school["attributes"]
    if not comparison and SAMPLE_SCHOOLS:
        # Return two schools by default for comparison views
        for school in SAMPLE_SCHOOLS[:2]:
            comparison[school["name"]] = school["attributes"]
    return comparison


def get_sample_cost_benefit(intervention_name: str, metric_name: str, intervention_cost: float | None = None) -> Dict[str, object]:
    """Generate sample cost-benefit analysis data."""
    if intervention_cost is None:
        default_costs = {
            "teacher_training": 5000.0,
            "mentoring": 3000.0,
            "workshop": 2000.0,
            "coaching": 4000.0,
        }
        intervention_cost = default_costs.get(intervention_name.lower(), 3000.0)
    
    # Sample improvement data
    participants = 45
    avg_improvement = 2.3  # Points improvement
    total_cost = intervention_cost * participants
    value_per_point = 100.0
    total_value = avg_improvement * participants * value_per_point
    roi = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0.0
    
    return {
        "intervention": intervention_name,
        "metric": metric_name,
        "participants": participants,
        "average_improvement": round(avg_improvement, 2),
        "median_improvement": round(avg_improvement * 0.95, 2),
        "cost_per_participant": round(intervention_cost, 2),
        "total_cost": round(total_cost, 2),
        "cost_per_improvement_unit": round(total_cost / avg_improvement, 2),
        "roi_percentage": round(roi, 2),
        "total_value_generated": round(total_value, 2),
        "generated_at": _timestamp(),
        "sample": True,
    }

