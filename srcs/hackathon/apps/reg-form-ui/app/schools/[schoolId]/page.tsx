// app/schools/[schoolId]/page.tsx (Server Component)

import SchoolDashboard from "@/components/school-dashboard"; // Assuming you moved your component here
import { notFound } from "next/navigation";

// You might need to add a "use client" directive to the imported SchoolDashboard
// component itself if it uses client-side hooks (like useState/useEffect) or recharts.

// Define props for the dynamic segment
interface SchoolDashboardPageProps {
  params: {
    schoolId: string;
  };
}

// Mock data fetch for a single school (replace with your actual API fetch)
const fetchSchoolData = async (id: string) => {
  // In a real application, fetch data specific to this ID
  if (id === "S001") {
    return {
      name: "Lincoln Elementary School",
      // ... all the data needed for the dashboard
    };
  }
  // Return null or throw error if not found
  return null;
};

export default async function SchoolDashboardPage({
  params,
}: SchoolDashboardPageProps) {
  const schoolId = params.schoolId;
  const schoolData = await fetchSchoolData(schoolId);

  if (!schoolData) {
    // Next.js helper to show the standard 404 page
    notFound();
  }

  // Handlers for the dashboard component
  // Since we are using an App Router route, onBack should navigate back
  const handleBack = () => {
    // In a client component, you would use router.back()
    // Since this is a server component, the logic is passed to the client component
    // The SchoolDashboard component will need to use `useRouter().back()` for this to work.
  };

  const handleNewIntervention = () => {
    // Logic for opening a new intervention form (likely client-side)
    console.log(`Navigating to New Intervention Form for ${schoolId}`);
  };

  return <SchoolDashboard schoolId={schoolId} />;
}

// // Optional: Add `generateStaticParams` to pre-render common schools at build time
// export async function generateStaticParams() {
//   const schools = await getSchoolList(); // Re-use the list function
//   return schools.map((school) => ({
//     schoolId: school.id,
//   }));
// }
