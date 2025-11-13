"use client";
import { useRouter } from "next/navigation"; // <-- Use 'next/navigation'
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ChevronLeft, Plus } from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import InterventionTableRow from "./intervention-table-row";
import NewInterventionModal from "./new-intervention-modal";
import { useState } from "react";

interface SchoolDashboardProps {
  schoolId: string;
}

const mockSchoolData = {
  name: "Lincoln Elementary School",
  district: "Central District",
  students: 450,
  staff: 32,
  successRate: 78,
};

const trendsData = [
  { month: "Jan", success: 65, total: 12 },
  { month: "Feb", success: 70, total: 14 },
  { month: "Mar", success: 72, total: 16 },
  { month: "Apr", success: 75, total: 18 },
  { month: "May", success: 78, total: 22 },
  { month: "Jun", success: 80, total: 24 },
];

const interventionsData = [
  {
    id: 1,
    type: "Reading Support",
    students: 12,
    startDate: "2024-01-15",
    status: "Active",
    success: 82,
  },
  {
    id: 2,
    type: "Math Tutoring",
    students: 8,
    startDate: "2024-02-20",
    status: "Active",
    success: 75,
  },
  {
    id: 3,
    type: "Social-Emotional",
    students: 15,
    startDate: "2024-01-10",
    status: "Active",
    success: 80,
  },
  {
    id: 4,
    type: "Attendance Focus",
    students: 5,
    startDate: "2024-03-01",
    status: "Pending",
    success: 68,
  },
  {
    id: 5,
    type: "Behavioral Support",
    students: 6,
    startDate: "2023-12-05",
    status: "Completed",
    success: 76,
  },
];

export default function SchoolDashboard({ schoolId }: SchoolDashboardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleNewInterventionClick = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const router = useRouter(); // Initialize router
  // Define the interaction handlers *inside* the client component
  const handleBack = () => {
    router.back(); // Use the router for navigation
  };

  const handleNewIntervention = () => {
    // Navigate to a new route for the form
    router.push(`/schools/${schoolId}/new-intervention`);
  };
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <button
              onClick={handleBack}
              className="mb-4 flex items-center gap-2 text-accent hover:text-accent/80"
            >
              <ChevronLeft className="h-5 w-5" />
              Back
            </button>
            <h1 className="text-3xl font-bold text-foreground">
              {mockSchoolData.name}
            </h1>
            <p className="mt-1 text-muted-foreground">
              {mockSchoolData.district}
            </p>
          </div>
          <Button onClick={handleNewInterventionClick} className="gap-2">
            <Plus className="h-4 w-4" />
            New Intervention
          </Button>
          <NewInterventionModal
            isOpen={isModalOpen}
            onClose={handleCloseModal}
          />
        </div>

        {/* Key Metrics */}
        <div className="mb-8 grid gap-4 md:grid-cols-4">
          <Card className="border-border bg-card p-6">
            <p className="text-sm text-muted-foreground">Students</p>
            <p className="mt-2 text-3xl font-bold text-foreground">
              {mockSchoolData.students}
            </p>
          </Card>
          <Card className="border-border bg-card p-6">
            <p className="text-sm text-muted-foreground">Staff</p>
            <p className="mt-2 text-3xl font-bold text-foreground">
              {mockSchoolData.staff}
            </p>
          </Card>
          <Card className="border-border bg-card p-6">
            <p className="text-sm text-muted-foreground">
              Active Interventions
            </p>
            <p className="mt-2 text-3xl font-bold text-accent">
              {interventionsData.filter((i) => i.status === "Active").length}
            </p>
          </Card>
          <Card className="border-border bg-card p-6">
            <p className="text-sm text-muted-foreground">Success Rate</p>
            <p className="mt-2 text-3xl font-bold text-primary">
              {mockSchoolData.successRate}%
            </p>
          </Card>
        </div>

        {/* Charts */}
        <div className="mb-8 grid gap-6 lg:grid-cols-2">
          {/* Success Rate Trend */}
          <Card className="border-border bg-card p-6">
            <h3 className="mb-4 font-semibold text-foreground">
              Success Rate Trend
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis stroke="var(--muted-foreground)" />
                <YAxis stroke="var(--muted-foreground)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    border: "1px solid var(--border)",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="success"
                  stroke="var(--chart-1)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Interventions by Type */}
          <Card className="border-border bg-card p-6">
            <h3 className="mb-4 font-semibold text-foreground">
              Interventions by Month
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trendsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis stroke="var(--muted-foreground)" />
                <YAxis stroke="var(--muted-foreground)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    border: "1px solid var(--border)",
                  }}
                />
                <Legend />
                <Bar dataKey="total" fill="var(--chart-2)" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
        {/* Interventions Table */}
        <Card className="border-border bg-card p-6">
          <h3 className="mb-6 font-semibold text-foreground">
            All Interventions
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              {/* ... (table head <thead>) ... */}
              <tbody>
                {/* REPLACE the map logic with the new InterventionTableRow 
                  Since SchoolDashboard is already a Client Component, 
                  it can safely import and render another Client Component.
                */}
                {interventionsData.map((intervention) => (
                  <InterventionTableRow
                    key={intervention.id}
                    intervention={intervention}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
