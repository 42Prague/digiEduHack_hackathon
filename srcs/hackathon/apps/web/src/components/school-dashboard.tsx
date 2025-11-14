"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Plus, Users, TrendingUp, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

// Define the map outside of the component functions
const SCHOOL_NAME_MAP: { [key: string]: string } = {
  capek: "ZŠ Karla Čapka",
  jarov: "Scio škola Praha Jarov",
  hostinska: "Základní škola Hostýnská",
};

// Helper function to get the display name
const getDisplayName = (schoolNameKey: string): string => {
  return SCHOOL_NAME_MAP[schoolNameKey] || schoolNameKey;
};

// --- INTERFACE Definitions ---
export interface Intervention {
  _id: string; // Mongo ObjectId
  schoolName: string;
  interventionType: string;
  createdAt: string | { $date: string };
  processedData?: {
    overall_sentiment?: {
      polarity: "positive" | "negative" | "neutral";
      [key: string]: any;
    };
    [key: string]: any;
  };
  success?: boolean; // Derived from polarity
  type?: string; // Derived from interventionType
  [key: string]: any;
}

export interface SchoolData {
  id: string;
  name: string;
  totalInterventions: number;
  successRate: string;
  lastIntervention: string;
  interventions: Intervention[];
}

// --- InterventionDetail Component (Unchanged) ---
const InterventionDetail = ({
  intervention,
  onBack,
}: {
  intervention: Intervention;
  onBack: () => void;
}) => {
  const fullData = intervention as any;

  const formatDate = (date: string | { $date: string }) => {
    if (typeof date === "object" && "$date" in date) {
      return (
        new Date(date.$date).toLocaleDateString() +
        " " +
        new Date(date.$date).toLocaleTimeString()
      );
    }
    return (
      new Date(date).toLocaleDateString() +
      " " +
      new Date(date).toLocaleTimeString()
    );
  };

  return (
    <div className="p-6">
      <Button onClick={onBack} variant="outline" className="mb-4 gap-2">
        <ArrowLeft className="h-4 w-4" />
        Back to School History
      </Button>
      <h2 className="text-3xl font-bold mb-4">
        Intervention Detail: {fullData.interventionType}
      </h2>

      <div className="space-y-6">
        {/* Basic Info */}
        <Card className="p-4">
          <h4 className="text-xl font-semibold mb-3">Basic Information</h4>
          <div className="grid grid-cols-2 gap-y-2">
            <p>
              <span className="font-medium">School:</span>{" "}
              {getDisplayName(fullData.schoolName)}
            </p>
            <p>
              <span className="font-medium">Type:</span>{" "}
              {fullData.interventionType}
            </p>
            <p>
              <span className="font-medium">Date:</span>{" "}
              {formatDate(fullData.createdAt)}
            </p>
            <p>
              <span className="font-medium">Status:</span>
              <span
                className={`ml-1 font-bold ${fullData.success ? "text-green-600" : "text-red-600"}`}
              >
                {fullData.success ? "Success" : "Pending/Fail"}
              </span>
            </p>
          </div>
        </Card>

        {fullData.processedData && (
          <Card className="p-4">
            <h4 className="text-xl font-semibold mb-3">
              AI-Processed Data Summary
            </h4>
            <div className="space-y-4">
              <p>
                <span className="font-medium">Overall Sentiment Polarity:</span>{" "}
                <span className="font-bold">
                  {fullData.processedData.overall_sentiment.polarity.toUpperCase()}
                </span>{" "}
                (Confidence:{" "}
                {(
                  fullData.processedData.overall_sentiment.confidence * 100
                ).toFixed(0)}
                %)
              </p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

// --- SchoolDetail Component (Unchanged) ---
const SchoolDetail = ({
  school,
  onBack,
  onSelectIntervention,
}: {
  school: SchoolData;
  onBack: () => void;
  onSelectIntervention: (intervention: Intervention) => void;
}) => (
  <div className="p-6">
    <Button onClick={onBack} variant="outline" className="mb-4 gap-2">
      <ArrowLeft className="h-4 w-4" />
      Back to All Schools
    </Button>
    <h2 className="text-3xl font-bold">{school.name} History</h2>
    <p className="mt-2 text-lg text-muted-foreground">
      Total Interventions: {school.totalInterventions}
    </p>
    <Card className="mt-6 p-4">
      <h4 className="text-xl font-semibold mb-3">Interventions History</h4>
      {school.interventions.map((intervention) => (
        <Card
          key={intervention._id}
          className="p-3 mb-2 hover:bg-muted cursor-pointer transition-colors"
          onClick={() => onSelectIntervention(intervention)}
        >
          <div className="flex justify-between items-center">
            {/* Use the derived 'type' property */}
            <span className="font-medium">{intervention.type}</span>
            <span
              className={`text-sm ${intervention.success ? "text-green-600" : "text-red-600"}`}
            >
              {intervention.success ? "Success" : "Pending/Fail"}
            </span>
          </div>
        </Card>
      ))}
    </Card>
  </div>
);

// Helper function to format date difference (simplified for example)
const timeSince = (dateString: string): string => {
  const date = new Date(dateString);
  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);

  let interval = seconds / 31536000;
  if (interval > 1) return Math.floor(interval) + " years ago";
  interval = seconds / 2592000;
  if (interval > 1) return Math.floor(interval) + " months ago";
  interval = seconds / 86400;
  if (interval > 1) return Math.floor(interval) + " days ago";
  interval = seconds / 3600;
  if (interval > 1) return Math.floor(interval) + " hours ago";
  interval = seconds / 60;
  if (interval > 1) return Math.floor(interval) + " minutes ago";
  return Math.floor(seconds) + " seconds ago";
};

// --- Main Component ---
export default function SchoolDashboard({
  onNewIntervention,
}: {
  onNewIntervention: () => void;
}) {
  const [schoolsData, setSchoolsData] = useState<SchoolData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSchool, setSelectedSchool] = useState<SchoolData | null>(null);
  const [selectedIntervention, setSelectedIntervention] =
    useState<Intervention | null>(null);

  // 1. Data Fetching and Processing
  useEffect(() => {
    const fetchInterventions = async () => {
      try {
        setLoading(true);
        // Assuming your API route is at /api/interventions
        const response = await fetch("/api/interventions");
        if (!response.ok) throw new Error("Failed to fetch data");

        const { interventions }: { interventions: Intervention[] } =
          await response.json();

        // ----------------------------------------------------
        // 1. FIX APPLIED: Derive success from polarity (MAP)
        // ----------------------------------------------------
        const interventionsWithStatus = interventions.map((i: Intervention) => {
          // 1. Check if polarity is 'positive'
          const isSuccess =
            i.processedData?.overall_sentiment?.polarity === "positive";

          // 2. Handle Mongo $date object if present
          const createdAtDateString =
            typeof i.createdAt === "object" && "$date" in i.createdAt
              ? i.createdAt.$date
              : (i.createdAt as string);

          return {
            ...i,
            // Assign derived fields for component compatibility
            success: isSuccess,
            type: i.interventionType, // Map JSON field name to component field name
            createdAt: createdAtDateString,
          };
        });

        // -------------------------------------------------------------------------
        // 2. CORRECTED LOGIC: Aggregate data by schoolName (REDUCE)
        // Ensure you use the school KEY for the acc property and the display NAME for the SchoolData property
        // -------------------------------------------------------------------------
        const schoolMap = interventionsWithStatus.reduce(
          (acc, intervention) => {
            const key = intervention.schoolName; // e.g., 'capek' (use as the map key)
            const name = getDisplayName(key); // e.g., 'ZŠ Karla Čapka' (use as the display name)

            if (!acc[key]) {
              acc[key] = {
                id: key.replace(/\s/g, "-").toLowerCase(), // Use key for ID
                name: name, // Store the DISPLAY NAME here
                totalInterventions: 0,
                successfulCount: 0,
                interventions: [],
                lastTimestamp: 0,
              };
            }

            acc[key].totalInterventions++;
            if (intervention.success) acc[key].successfulCount++; // Use derived success
            acc[key].interventions.push(intervention);

            // Track the latest intervention date
            const currentTimestamp = new Date(
              intervention.createdAt as string
            ).getTime();
            if (currentTimestamp > acc[key].lastTimestamp) {
              acc[key].lastTimestamp = currentTimestamp;
            }

            return acc;
          },
          {} as Record<
            string,
            SchoolData & { successfulCount: number; lastTimestamp: number }
          >
        );

        // Finalize calculations
        const processedSchools = Object.values(schoolMap).map((school) => ({
          ...school,
          successRate: `${Math.round((school.successfulCount / school.totalInterventions) * 100)}%`,
          lastIntervention: timeSince(
            new Date(school.lastTimestamp).toISOString()
          ),
          // Sort interventions within the school by recency for detail view
          interventions: school.interventions.sort(
            (a, b) =>
              new Date(b.createdAt as string).getTime() -
              new Date(a.createdAt as string).getTime()
          ),
        }));

        setSchoolsData(processedSchools);
        setError(null);
      } catch (e) {
        console.error(e);
        setError("Could not load intervention data. Please check the API.");
        setSchoolsData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchInterventions();
  }, []);

  // 2. Global Statistics Calculation (Unchanged)
  const { totalSchools, totalInterventions, avgSuccessRate } = useMemo(() => {
    const totalSchools = schoolsData.length;
    const totalInterventions = schoolsData.reduce(
      (sum, s) => sum + s.totalInterventions,
      0
    );

    const successSum = schoolsData.reduce((sum, s) => {
      const rate = Number.parseInt(s.successRate.replace("%", ""));
      return sum + rate * s.totalInterventions;
    }, 0);

    const avgSuccessRate =
      totalInterventions > 0 ? Math.round(successSum / totalInterventions) : 0;

    return { totalSchools, totalInterventions, avgSuccessRate };
  }, [schoolsData]);

  // 3. Navigation Handlers (Unchanged)
  const handleSelectIntervention = useCallback((intervention: Intervention) => {
    setSelectedIntervention(intervention);
  }, []);

  // 4. Render Logic (List View vs. Detail View) (Unchanged)

  if (selectedIntervention) {
    return (
      <InterventionDetail
        intervention={selectedIntervention}
        onBack={() => setSelectedIntervention(null)}
      />
    );
  }

  if (selectedSchool) {
    return (
      <SchoolDetail
        school={selectedSchool}
        onBack={() => setSelectedSchool(null)}
        onSelectIntervention={handleSelectIntervention}
      />
    );
  }

  // School List View (Default)
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header and Stats Overview */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-foreground">
              School interventions
            </h1>
            <p className="mt-2 text-muted-foreground">
              Track and analyze interventions across your schools
            </p>
          </div>
          <Button
            onClick={onNewIntervention}
            className="gap-2 bg-accent hover:bg-accent/90 text-accent-foreground"
          >
            <Plus className="h-5 w-5" />
            New Intervention
          </Button>
        </div>

        {error && (
          <div className="p-4 mb-6 text-red-700 bg-red-100 border border-red-300 rounded">
            {error}
          </div>
        )}

        {/* Stats Overview */}
        <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card className="border-border bg-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Schools</p>
                <div className="mt-2 text-3xl font-bold text-foreground">
                  {loading ? <Skeleton className="h-8 w-20" /> : totalSchools}
                </div>
              </div>
              <Users className="h-8 w-8 text-accent" />
            </div>
          </Card>
          <Card className="border-border bg-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  Total Interventions
                </p>
                <div className="mt-2 text-3xl font-bold text-foreground">
                  {loading ? (
                    <Skeleton className="h-8 w-20" />
                  ) : (
                    totalInterventions
                  )}
                </div>
              </div>
              <TrendingUp className="h-8 w-8 text-primary" />
            </div>
          </Card>
        </div>

        {/* Schools List/Grid */}
        <div className="grid gap-4 lg:grid-cols-1">
          <h2 className="text-2xl font-semibold mb-4 text-foreground">
            School Performance Overview
          </h2>

          {loading ? (
            <div className="space-y-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : schoolsData.length === 0 ? (
            <p className="text-center text-muted-foreground">
              No schools found. Add your first intervention!
            </p>
          ) : (
            schoolsData.map((school) => (
              <Card
                key={school.id}
                className="border-border bg-card p-6 transition-all hover:border-primary/50 cursor-pointer"
                onClick={() => setSelectedSchool(school)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-foreground">
                      {school.name}
                    </h3>
                    <div className="mt-4 flex gap-6">
                      <div>
                        <p className="text-2xl font-semibold text-foreground">
                          {school.totalInterventions}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Interventions
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">
                      Last Update: {school.lastIntervention}
                    </p>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
