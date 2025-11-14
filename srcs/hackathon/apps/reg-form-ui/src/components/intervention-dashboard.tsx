"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  BarChart, // Kept for Sentiment by Aspect - will convert to list/badges in code
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Users,
  FileText,
  TrendingUp,
  Sparkles,
  ThumbsUp,
  ThumbsDown,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

// --- Utility Functions/Components for Descriptive Sentiment ---

/**
 * Returns the appropriate color class for sentiment badges/text.
 * @param {string} sentiment - 'positive' or 'negative'.
 * @returns {string} Tailwind CSS classes.
 */
const getSentimentClasses = (sentiment: string) => {
  return sentiment === "positive"
    ? "bg-green-500/10 text-green-500 border-green-500/30" // Primary success color
    : "bg-red-500/10 text-red-500 border-red-500/30"; // Primary destructive color
};

/**
 * Custom component to display Sentiment by Aspect as a descriptive list.
 */
function SentimentByAspectList({
  data,
}: {
  data: Array<{ aspect: string; sentiment: string }>;
}) {
  return (
    <div className="space-y-3">
      {data.map((item, index) => (
        <div
          key={index}
          className="flex justify-between items-center p-3 rounded-lg border border-border transition-colors hover:bg-muted/30"
        >
          <span className="text-sm font-medium text-foreground max-w-[70%]">
            {item.aspect}
          </span>
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${getSentimentClasses(item.sentiment)}`}
          >
            {item.sentiment === "positive" ? (
              <ThumbsUp className="h-3 w-3" />
            ) : (
              <ThumbsDown className="h-3 w-3" />
            )}
            {item.sentiment.charAt(0).toUpperCase() + item.sentiment.slice(1)}
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Custom component to display Emotional Tone as descriptive badges.
 */
function EmotionalToneBadges({ tones }: { tones: string[] }) {
  const getToneClass = (tone: string) => {
    // Simple logic: enthusiasm/hope are positive, frustration is negative, others neutral
    if (tone.toLowerCase() === "enthusiasm" || tone.toLowerCase() === "hope") {
      return "bg-blue-500/10 text-blue-500 border-blue-500/30";
    }
    if (tone.toLowerCase() === "frustration") {
      return "bg-orange-500/10 text-orange-500 border-orange-500/30";
    }
    return "bg-muted text-muted-foreground border-border";
  };

  return (
    <div className="flex flex-wrap gap-2">
      {tones.map((tone, index) => (
        <div
          key={index}
          className={`px-3 py-1 rounded-full text-sm font-medium border ${getToneClass(tone)}`}
        >
          <Zap className="h-3 w-3 inline mr-1" />
          {tone.charAt(0).toUpperCase() + tone.slice(1)}
        </div>
      ))}
    </div>
  );
}

// --- Original Interface and Main Component ---

interface Intervention {
  _id?: string;
  schoolName: string;
  regionName: string;
  guideName: string;
  interventionType: string;
  listOfParticipants?: {
    schoolStaff: Array<{ name: string; age: number; grade: string }>;
    mentors: Array<any>;
  };
  processedData?: {
    overall_sentiment: {
      confidence: number;
      emotional_tone: string[];
      polarity: string;
    };
    sentiment_by_aspect: Array<{ aspect: string; sentiment: string }>;
    impact_assessment: {
      on_school_culture: { scope: string; mentioned: boolean; changes: any[] };
      on_students: {
        type: string;
        examples: any[];
        direction: string;
        mentioned: boolean;
      };
      on_teacher: { professional_growth: string; confidence_level: string };
    };
    theme_extraction: {
      pedagogical_concepts: string[];
      challenges_mentioned: string[];
    };
  };
  createdAt: string;
}

export function InterventionDashboard() {
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIntervention, setSelectedIntervention] =
    useState<Intervention | null>(null);

  useEffect(() => {
    const fetchInterventions = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/interventions");

        if (!response.ok) {
          throw new Error(
            `Failed to fetch interventions: ${response.statusText}`
          );
        }

        const data = await response.json();
        setInterventions(data.interventions);

        // Set the first intervention as selected
        if (data.interventions.length > 0) {
          setSelectedIntervention(data.interventions[0]);
        }
      } catch (err) {
        console.error("[v0] Error fetching interventions:", err);
        setError(
          err instanceof Error ? err.message : "Failed to fetch interventions"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchInterventions();
  }, []);

  const interventionData = selectedIntervention || {
    schoolName: "No Data Available",
    interventionType: "N/A",
    regionName: "N/A",
    guideName: "N/A",
    createdAt: new Date().toISOString(),
    listOfParticipants: { schoolStaff: [], mentors: [] },
    processedData: {
      overall_sentiment: {
        confidence: 0,
        emotional_tone: [],
        polarity: "neutral",
      },
      sentiment_by_aspect: [],
      impact_assessment: {
        on_school_culture: { scope: "", mentioned: false, changes: [] },
        on_students: {
          type: "",
          examples: [],
          direction: "",
          mentioned: false,
        },
        on_teacher: { professional_growth: "", confidence_level: "" },
      },
      theme_extraction: { pedagogical_concepts: [], challenges_mentioned: [] },
    },
  };

  // --- Simplified Data Processing for New Descriptive Format ---

  // SentimentByAspect: Directly use the raw array
  const sentimentByAspectData =
    interventionData.processedData?.sentiment_by_aspect || [];

  // EmotionalTone: Directly use the raw array
  const emotionalToneData =
    interventionData.processedData?.overall_sentiment?.emotional_tone || [];

  // Overall Sentiment for the Pie Chart (kept for context, but can be removed if a fully descriptive approach is desired)
  const sentimentData =
    interventionData.processedData?.overall_sentiment?.polarity === "positive"
      ? [
          { name: "Positive", value: 3, fill: "#8b5cf6" },
          { name: "Negative", value: 1, fill: "#ec4899" },
        ]
      : [
          { name: "Positive", value: 1, fill: "#8b5cf6" },
          { name: "Negative", value: 3, fill: "#ec4899" },
        ];

  // Key Metrics Calculations (kept as is)
  const participantCount =
    interventionData.listOfParticipants?.schoolStaff?.length || 0;
  const confidenceScore = interventionData.processedData?.overall_sentiment
    ?.confidence
    ? (
        interventionData.processedData.overall_sentiment.confidence * 100
      ).toFixed(0)
    : "0";
  const positiveAspects = (
    interventionData.processedData?.sentiment_by_aspect || []
  ).filter((item: any) => item.sentiment === "positive").length;
  const conceptCount =
    interventionData.processedData?.theme_extraction?.pedagogical_concepts
      ?.length || 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">Loading intervention data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <div className="text-center">
          <p className="text-destructive">Error: {error}</p>
        </div>
      </div>
    );
  }

  const SCHOOL_NAME_MAP: { [key: string]: string } = {
    capek: "ZŠ Karla Čapka",
    jarov: "Scio škola Praha Jarov",
    hostinska: "Základní škola Hostýnská",
  };

  const displaySchoolName =
    SCHOOL_NAME_MAP[interventionData.schoolName] || interventionData.schoolName;

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        {interventions.length > 1 && (
          <div className="mb-6 p-4 bg-card border border-border rounded-lg">
            <label className="text-sm text-muted-foreground block mb-2">
              Select Intervention:
            </label>
            <select
              value={selectedIntervention?._id || ""}
              onChange={(e) => {
                const intervention = interventions.find(
                  (i) => i._id === e.target.value
                );
                setSelectedIntervention(intervention || null);
              }}
              className="w-full max-w-md px-3 py-2 bg-input border border-border rounded-md text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {interventions.map((intervention) => (
                <option key={intervention._id} value={intervention._id}>
                  {/*
                    *** THIS IS THE CHANGE ***
                    We use the map to translate intervention.schoolName for the dropdown text.
                  */}
                  {SCHOOL_NAME_MAP[intervention.schoolName] ||
                    intervention.schoolName}{" "}
                  - {intervention.interventionType}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2 text-balance">
            {displaySchoolName} - intervention
          </h1>
          <p className="text-muted-foreground text-lg">
            {interventionData.interventionType} program •{" "}
            {interventionData.regionName} region
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card className="bg-card border-border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Participants
              </CardTitle>
              <Users className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                {participantCount}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                School staff members
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Confidence Score
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-accent" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                {confidenceScore}%
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Analysis confidence level
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Positive Aspects
              </CardTitle>
              <Sparkles className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                {positiveAspects}/{sentimentByAspectData.length}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Positive sentiment areas
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Key Themes
              </CardTitle>
              <FileText className="h-4 w-4 text-secondary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                {conceptCount}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Pedagogical concepts identified
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Sentiment Row - Overall Sentiment Chart (retained) and Emotional Tone (changed) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Sentiment Overview (Retained Pie Chart) */}
          {/* <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-foreground">
                Overall Sentiment Polarity
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                Distribution of feedback polarity
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={sentimentData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name} (${value})`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {sentimentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card> */}

          {/* Emotional Tone (Changed to Descriptive Badges) */}
        </div>

        {/* Charts Row 2 - Sentiment by Aspect (changed) and Impact Assessment (retained) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Sentiment by Aspect (Changed to Descriptive List) */}
          <Card className="lg:col-span-2 bg-card border-border">
            <CardHeader>
              <CardTitle className="text-foreground">
                Sentiment by Aspect
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                Feedback across different program dimensions (+/-)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SentimentByAspectList data={sentimentByAspectData} />
            </CardContent>
          </Card>

          {/* Impact Assessment (Retained) */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-foreground text-base">
                Impact Assessment
              </CardTitle>
              <CardDescription className="text-muted-foreground text-sm">
                Key areas of influence
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Teacher Growth
                  </span>
                  <span className="text-sm font-semibold text-primary">
                    {interventionData.processedData?.impact_assessment
                      ?.on_teacher?.professional_growth || "N/A"}
                  </span>
                </div>
                {/* Visual cues for impact - static length retained for placeholder */}
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary w-4/5" />
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Confidence Level
                  </span>
                  <span className="text-sm font-semibold text-secondary">
                    {interventionData.processedData?.impact_assessment
                      ?.on_teacher?.confidence_level || "N/A"}
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-secondary w-3/5" />
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Student Impact
                  </span>
                  <span className="text-sm font-semibold text-accent">
                    {interventionData.processedData?.impact_assessment
                      ?.on_students?.direction || "N/A"}
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-accent w-4/5" />
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    School Culture
                  </span>
                  <span className="text-sm font-semibold text-primary">
                    {interventionData.processedData?.impact_assessment
                      ?.on_school_culture?.scope || "N/A"}
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary w-1/2" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Key Themes and Challenges (Retained) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pedagogical Concepts */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-foreground">
                Key Pedagogical Themes
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                Main teaching and learning concepts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {(
                  interventionData.processedData?.theme_extraction
                    ?.pedagogical_concepts || []
                )
                  .slice(0, 12)
                  .map((concept: string, idx: number) => (
                    <div
                      key={idx}
                      className="px-3 py-1 rounded-full bg-primary/10 border border-primary/30 text-xs text-primary font-medium"
                    >
                      {concept}
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          {/* Challenges */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-foreground">Main Challenges</CardTitle>
              <CardDescription className="text-muted-foreground">
                Identified barriers to implementation
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {(
                interventionData.processedData?.theme_extraction
                  ?.challenges_mentioned || []
              ).map((challenge: string, idx: number) => (
                <div key={idx} className="flex gap-3">
                  <div className="h-6 w-6 rounded-full bg-accent/20 border border-accent flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-accent">
                      {idx + 1}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground pt-0.5">
                    {challenge}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Program Details (Retained) */}
        <Card className="bg-card border-border mt-8">
          <CardHeader>
            <CardTitle className="text-foreground">
              Program Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div>
                  <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide">
                    School
                  </p>
                  <p className="text-sm text-foreground mt-1">
                    {/* USE THE TRANSLATED NAME HERE */}
                    {displaySchoolName}
                  </p>
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide">
                  Region
                </p>
                <p className="text-sm text-foreground mt-1">
                  {interventionData.regionName}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide">
                  Program Guide
                </p>
                <p className="text-sm text-foreground mt-1">
                  {interventionData.guideName}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide">
                  Created
                </p>
                <p className="text-sm text-foreground mt-1">
                  {new Date(interventionData.createdAt).toLocaleDateString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
