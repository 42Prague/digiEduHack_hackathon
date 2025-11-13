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
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <p className="text-gray-600 mt-2">Welcome back, <span className="font-semibold">{session.user.name}</span>!</p>
      </div>
      
      {/* Admin Info Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Your Admin Profile</h2>
        <div className="p-4 bg-blue-50 rounded-lg">
          <ul className="space-y-2 text-sm text-gray-700">
            <li><span className="font-semibold">Email:</span> {session.user.email}</li>
            <li><span className="font-semibold">Role:</span> <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded">Admin</span></li>
            <li><span className="font-semibold">User ID:</span> {session.user.id}</li>
          </ul>
        </div>
      </div>

      {/* Admin Stats Card - demonstrates using adminProcedure from client */}
      <AdminStatsCard />
    </div>
  );
}