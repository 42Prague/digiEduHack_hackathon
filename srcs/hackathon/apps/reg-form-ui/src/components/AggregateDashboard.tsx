// components/AggregateDashboard.tsx
"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { mockAggregateData } from "@/lib/data"; // Replace with actual aggregate data

// Recharts chart component
function TopSkillsChart({ data }: { data: typeof mockAggregateData }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={data}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        layout="vertical"
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis dataKey="name" type="category" width={80} />
        <Tooltip />
        <Bar
          dataKey="count"
          fill="#3b82f6"
          name="Job Count"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function AggregateDashboard() {
  // In a real app, this data would be fetched and processed from your array of job objects
  const skillsData = mockAggregateData;

  return (
    <div className="space-y-6 p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold">Job Market Insights Dashboard 📈</h1>
      <p className="text-lg text-muted-foreground">
        Insights derived from {skillsData.length * 10} enriched job
        advertisements.
      </p>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Chart 1: Top Required Skills */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Top 5 Required Core Technologies</CardTitle>
          </CardHeader>
          <CardContent>
            <TopSkillsChart data={skillsData} />
          </CardContent>
        </Card>

        {/* Metric 1: Average Salary */}
        <Card>
          <CardHeader>
            <CardTitle>Avg. Senior Developer Salary (CZK)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">145,000 CZK</div>
            <p className="text-xs text-muted-foreground">+5% vs Last Quarter</p>
          </CardContent>
        </Card>

        {/* Metric 2: Remote Jobs Percentage */}
        <Card>
          <CardHeader>
            <CardTitle>Remote vs. Onsite Split</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">35% Remote</div>
            {/* Placeholder for a simple doughnut chart */}
            <div className="h-4 w-full bg-blue-100 rounded-full mt-2">
              <div
                style={{ width: "35%" }}
                className="h-full bg-blue-600 rounded-full"
              ></div>
            </div>
            <p className="text-xs text-muted-foreground">
              75% Hybrid/Fully Remote options available.
            </p>
          </CardContent>
        </Card>

        {/* Metric 3: Jobs in Fintech/E-commerce */}
        <Card>
          <CardHeader>
            <CardTitle>Industry Demand</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">Fintech/Payments</div>
            <p className="text-xs text-muted-foreground">
              #1 most demanded vertical (22% of jobs)
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
