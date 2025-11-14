"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowLeft, Calendar } from "lucide-react";

interface Survey {
  timepoint: string;
  sentiment: "positive" | "neutral" | "negative";
  sentimentScore: number;
  keywords: {
    positive: string[];
    negative: string[];
  };
}

interface SchoolApplication {
  id: string;
  name: string;
  appliedDate: string;
  surveys: Survey[];
}

interface InterventionDetailProps {
  interventionId: string;
  schoolId: string;
  onBack: () => void;
  onSelectSchool: (schoolId: string) => void;
}

const mockInterventionData: Record<
  string,
  Record<
    string,
    {
      name: string;
      description: string;
      appliedDate: string;
      surveys: Survey[];
    }
  >
> = {
  "1": {
    s1: {
      name: "Differentiated Instruction",
      description:
        "A teaching approach that involves tailoring instruction to meet individual student needs, abilities, and learning styles. This intervention includes training for teachers on assessment techniques and adaptive teaching strategies.",
      appliedDate: "2025-10-15",
      surveys: [
        {
          timepoint: "Immediate (2 days after)",
          sentiment: "positive",
          sentimentScore: 85,
          keywords: {
            positive: [
              "engaging",
              "students responded well",
              "practical",
              "clear examples",
            ],
            negative: [],
          },
        },
        {
          timepoint: "3 months after",
          sentiment: "positive",
          sentimentScore: 78,
          keywords: {
            positive: [
              "improved engagement",
              "better results",
              "easier to manage",
            ],
            negative: ["time consuming", "requires preparation"],
          },
        },
      ],
    },
    s2: {
      name: "Differentiated Instruction",
      description:
        "A teaching approach that involves tailoring instruction to meet individual student needs, abilities, and learning styles.",
      appliedDate: "2025-11-05",
      surveys: [
        {
          timepoint: "Immediate (2 days after)",
          sentiment: "positive",
          sentimentScore: 82,
          keywords: {
            positive: ["innovative", "teachers excited", "clear benefits"],
            negative: [],
          },
        },
      ],
    },
    s3: {
      name: "Differentiated Instruction",
      description:
        "A teaching approach that involves tailoring instruction to meet individual student needs, abilities, and learning styles.",
      appliedDate: "2025-09-20",
      surveys: [
        {
          timepoint: "Immediate (2 days after)",
          sentiment: "positive",
          sentimentScore: 88,
          keywords: {
            positive: ["excellent", "transformative", "highly effective"],
            negative: [],
          },
        },
        {
          timepoint: "6 months after",
          sentiment: "positive",
          sentimentScore: 81,
          keywords: {
            positive: [
              "sustained improvement",
              "student outcomes",
              "teacher confidence",
            ],
            negative: ["occasional challenges"],
          },
        },
      ],
    },
  },
  "2": {
    s4: {
      name: "Growth Mindset Training",
      description:
        "Teaching students to embrace challenges and learn from failures.",
      appliedDate: "2025-11-01",
      surveys: [
        {
          timepoint: "Immediate (2 days after)",
          sentiment: "positive",
          sentimentScore: 76,
          keywords: {
            positive: ["motivating", "student mindset shift"],
            negative: ["requires reinforcement"],
          },
        },
      ],
    },
    s5: {
      name: "Growth Mindset Training",
      description:
        "Teaching students to embrace challenges and learn from failures.",
      appliedDate: "2025-10-10",
      surveys: [
        {
          timepoint: "Immediate (2 days after)",
          sentiment: "positive",
          sentimentScore: 79,
          keywords: {
            positive: ["transformative", "positive feedback"],
            negative: [],
          },
        },
      ],
    },
    s1: {
      name: "Growth Mindset Training",
      description:
        "Teaching students to embrace challenges and learn from failures.",
      appliedDate: "2025-08-30",
      surveys: [
        {
          timepoint: "Immediate (2 days after)",
          sentiment: "positive",
          sentimentScore: 71,
          keywords: {
            positive: ["good start"],
            negative: ["complex concepts"],
          },
        },
      ],
    },
  },
};

export default function InterventionDetail({
  interventionId,
  schoolId,
  onBack,
}: InterventionDetailProps) {
  const data = mockInterventionData[interventionId]?.[schoolId];

  if (!data) {
    return <div>Intervention data not found</div>;
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "text-green-500";
      case "negative":
        return "text-red-500";
      default:
        return "text-yellow-500";
    }
  };

  const getSentimentBgColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "bg-green-500/10";
      case "negative":
        return "bg-red-500/10";
      default:
        return "bg-yellow-500/10";
    }
  };

  return (
    <main className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-4xl">
        <Button onClick={onBack} variant="ghost" className="mb-6 gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Schools
        </Button>

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">{data.name}</h1>
          <p className="mt-2 text-muted-foreground">{data.description}</p>
          <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar className="h-4 w-4" />
            Applied on {data.appliedDate}
          </div>
        </div>

        <Card className="border border-border bg-card p-6">
          <h2 className="text-xl font-semibold text-foreground mb-6">
            Survey Results
          </h2>

          {/* Surveys Timeline */}
          <div className="space-y-6">
            {data.surveys.map((survey, idx) => (
              <div key={idx} className="border-l-2 border-border pl-4">
                {/* Timepoint */}
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">
                    {survey.timepoint}
                  </span>
                  <div
                    className={`flex items-center gap-2 rounded px-3 py-1 ${getSentimentBgColor(survey.sentiment)}`}
                  >
                    <span
                      className={`font-semibold ${getSentimentColor(survey.sentiment)}`}
                    >
                      {survey.sentimentScore}% Positive
                    </span>
                  </div>
                </div>

                {/* Keywords */}
                <div className="grid gap-3 md:grid-cols-2">
                  {survey.keywords.positive.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-green-500 mb-2">
                        Positive Feedback
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {survey.keywords.positive.map((keyword, i) => (
                          <span
                            key={i}
                            className="inline-block rounded-full bg-green-500/20 px-3 py-1 text-xs text-green-300"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {survey.keywords.negative.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-red-500 mb-2">
                        Concerns
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {survey.keywords.negative.map((keyword, i) => (
                          <span
                            key={i}
                            className="inline-block rounded-full bg-red-500/20 px-3 py-1 text-xs text-red-300"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </main>
  );
}
