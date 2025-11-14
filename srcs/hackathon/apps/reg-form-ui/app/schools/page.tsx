// app/schools/page.tsx (Server Component)

// We don't need the school list fetch or the Link components here anymore,
// because the new SchoolDashboard handles the listing and click logic
// (switching between list and detail view).

import SchoolsClientWrapper from "./schools-client-wrapper";

// Note: This page is still a Server Component by default,
// which is good for performance and SEO.
export default function SchoolsPage() {
  return (
    // The Client Component handles all the logic:
    // data fetching, school list rendering, and detail view navigation.
    <SchoolsClientWrapper />
  );
}
