"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowRight, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import NewInterventionModal from "./new-intervention-modal";

interface Intervention {
  id: string;
  name: string;
  description: string;
  schoolsCount: number;
  adoptionRate: number;
  lastApplied: string;
}

const mockInterventions: Intervention[] = [
  {
    id: "1",
    name: "Differentiated Instruction",
    description: "Adapting teaching methods to meet individual student needs",
    schoolsCount: 5,
    adoptionRate: 85,
    lastApplied: "2025-11-10",
  },
  {
    id: "2",
    name: "Growth Mindset Training",
    description:
      "Teaching students to embrace challenges and learn from failures",
    schoolsCount: 3,
    adoptionRate: 72,
    lastApplied: "2025-10-15",
  },
  {
    id: "3",
    name: "Collaborative Learning",
    description: "Implementing peer-to-peer learning and group projects",
    schoolsCount: 7,
    adoptionRate: 91,
    lastApplied: "2025-11-08",
  },
  {
    id: "4",
    name: "Digital Literacy",
    description: "Integrating technology tools in classroom teaching",
    schoolsCount: 4,
    adoptionRate: 68,
    lastApplied: "2025-09-20",
  },
];

export default function InterventionsList() {
  const router = useRouter();

  // FIX 1: Defined handleNewIntervention
  const handleNewIntervention = () => {
    // Logic for logging a new intervention (e.g., navigate to a create form)
    router.push("/interventions/new");
  };

  // FIX 2: Added type annotation (string) to the 'id' parameter
  const handleRowClick = (id: string) => {
    // Navigate to the dynamic route for the specific intervention ID
    router.push(`/interventions/${id}`);
  };

  return (
    <main className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-12 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">
              Interventions
            </h1>
            <p className="mt-2 text-muted-foreground">
              Track teaching interventions across schools
            </p>
          </div>
          {/* Button now uses the defined handler */}
          <Button onClick={handleNewIntervention} className="gap-2">
            <Plus className="h-4 w-4" />
            Log Intervention
          </Button>
        </div>

        {/* Interventions Grid */}
        <div className="grid gap-6">
          {mockInterventions.map((intervention) => (
            <Card
              key={intervention.id}
              className="overflow-hidden border border-border bg-card p-6 hover:bg-card/80 cursor-pointer transition-colors"
              onClick={() => handleRowClick(intervention.id)}
            >
              <div className="flex items-start justify-between gap-6">
                <div className="flex-1">
                  <h2 className="text-xl font-semibold text-card-foreground">
                    {intervention.name}
                  </h2>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {intervention.description}
                  </p>

                  {/* Stats */}
                  <div className="mt-4 flex gap-8">
                    <div>
                      <div className="text-sm text-muted-foreground">
                        Schools
                      </div>
                      <div className="text-2xl font-bold text-accent">
                        {intervention.schoolsCount}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">
                        Adoption Rate
                      </div>
                      <div className="text-2xl font-bold text-accent">
                        {intervention.adoptionRate}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">
                        Last Applied
                      </div>
                      <div className="text-sm font-semibold text-card-foreground">
                        {intervention.lastApplied}
                      </div>
                    </div>
                  </div>
                </div>

                <ArrowRight className="h-6 w-6 text-muted-foreground flex-shrink-0 mt-1" />
              </div>
            </Card>
          ))}
        </div>
      </div>
    </main>
  );
}
