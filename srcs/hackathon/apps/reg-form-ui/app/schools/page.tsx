// app/schools/page.tsx (Server Component)

import Link from "next/link";
import { Card } from "@/components/ui/card"; // Assuming your card component
import { ArrowRight } from "lucide-react";

// Define types (can be shared from a separate file)
interface School {
  id: string;
  name: string;
  district: string;
}

// Mock data fetch (Replace with your actual API fetch)
const getSchoolList = async (): Promise<School[]> => {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 500));
  return [
    { id: "S001", name: "Lincoln Elementary", district: "Central District" },
    { id: "S002", name: "Washington Middle", district: "Westside Unified" },
    { id: "S003", name: "Jefferson High", district: "Central District" },
  ];
};

export default async function SchoolsListPage() {
  const schools = await getSchoolList();

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Select a School</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {schools.map((school) => (
          // Use Next.js Link component to navigate to the dynamic route
          <Link
            key={school.id}
            href={`/schools/${school.id}`}
            className="group block" // Apply necessary styling for link wrapping
          >
            <Card className="border-border bg-card p-6 transition-all hover:border-primary hover:shadow-lg cursor-pointer flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-foreground">
                  {school.name}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {school.district}
                </p>
              </div>
              <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
