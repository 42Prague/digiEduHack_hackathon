"use client";

import SchoolDashboard from "@/components/school-dashboard"; // Adjust the path as needed
import { useRouter } from "next/navigation";

// This component provides the context (e.g., router) needed
// for the SchoolDashboard's interactivity (onNewIntervention)
export default function SchoolsClientWrapper() {
  const router = useRouter();

  // Function to navigate when "New Intervention" is clicked
  const handleNewIntervention = () => {
    // Navigate to a dedicated page for creating a new intervention
    router.push("/interventions/new");
  };

  return (
    // The SchoolDashboard handles its own data fetching, state, and
    // the list-to-detail view transition.
    <SchoolDashboard onNewIntervention={handleNewIntervention} />
  );
}
