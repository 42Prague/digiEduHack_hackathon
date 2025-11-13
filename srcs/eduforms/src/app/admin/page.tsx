import { redirect } from "next/navigation";
import { auth } from "~/server/better-auth";
import { headers } from "next/headers";
import { AdminStatsCard } from "./_components/AdminStatsCard";

export default async function AdminPage() {
  // Get session on the server side (Node.js runtime - can access database)
  const session = await auth.api.getSession({
    headers: await headers(),
  });

  // Verify admin access - middleware only checks for session cookie
  // This is the authoritative check for admin role
  if (!session?.user || session.user.role !== "admin") {
    redirect("/");
  }

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>
      
      <div className="space-y-6">
        {/* Admin Info Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-lg mb-4">
            Welcome, <span className="font-semibold">{session.user.name}</span>!
          </p>
          <p className="text-gray-600">
            You have admin access. This page is protected and only accessible to admin users.
          </p>
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h2 className="font-semibold mb-2">Admin Information:</h2>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              <li>Email: {session.user.email}</li>
              <li>Role: {session.user.role}</li>
              <li>User ID: {session.user.id}</li>
            </ul>
          </div>
        </div>

        {/* Admin Stats Card - demonstrates using adminProcedure from client */}
        <AdminStatsCard />
      </div>
    </div>
  );
}