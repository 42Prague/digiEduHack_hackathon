"use client";

import { Plus, Users, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import SchoolDashboard from "./school-dashboard";

interface SchoolsListProps {
  onNewIntervention: () => void;
  onSelectSchool: (schoolId: string) => void;
}

const mockSchools = [
  {
    id: "1",
    name: "Lincoln Elementary School",
    district: "Central District",
    interventions: 24,
    successRate: "78%",
    lastUpdate: "2 hours ago",
  },
  {
    id: "2",
    name: "Jefferson Middle School",
    district: "East District",
    interventions: 17,
    successRate: "82%",
    lastUpdate: "5 hours ago",
  },
  {
    id: "3",
    name: "Washington High School",
    district: "West District",
    interventions: 31,
    successRate: "71%",
    lastUpdate: "1 hour ago",
  },
  {
    id: "4",
    name: "Roosevelt Secondary",
    district: "North District",
    interventions: 12,
    successRate: "85%",
    lastUpdate: "3 hours ago",
  },
];

export default function SchoolsList({
  onNewIntervention,
  onSelectSchool,
}: SchoolsListProps) {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-foreground">
              Educational Intervention Manager
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

        {/* Stats Overview */}
        <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card className="border-border bg-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Schools</p>
                <p className="mt-2 text-3xl font-bold text-foreground">
                  {mockSchools.length}
                </p>
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
                <p className="mt-2 text-3xl font-bold text-foreground">
                  {mockSchools.reduce((sum, s) => sum + s.interventions, 0)}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-primary" />
            </div>
          </Card>
          <Card className="border-border bg-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  Avg Success Rate
                </p>
                <p className="mt-2 text-3xl font-bold text-foreground">
                  {Math.round(
                    mockSchools.reduce(
                      (sum, s) => sum + Number.parseInt(s.successRate),
                      0
                    ) / mockSchools.length
                  )}
                  %
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-secondary" />
            </div>
          </Card>
        </div>

        {/* Schools Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1">
          {mockSchools.map((school) => (
            <Card
              key={school.id}
              className="border-border bg-card p-6 transition-all hover:border-primary/50 cursor-pointer"
              onClick={() => <SchoolDashboard schoolId={School} >}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-foreground">
                    {school.name}
                  </h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {school.district}
                  </p>
                  <div className="mt-4 flex gap-6">
                    <div>
                      <p className="text-2xl font-bold text-accent">
                        {school.interventions}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Interventions
                      </p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-primary">
                        {school.successRate}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Success Rate
                      </p>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">
                    {school.lastUpdate}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
