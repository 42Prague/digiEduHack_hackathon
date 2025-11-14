import { redirect } from "next/navigation";
import { auth } from "~/server/better-auth";
import { headers } from "next/headers";
import { UsersPageClient } from "./_components/UsersPageClient";

export default async function UsersPage() {
  // Get session on the server side (Node.js runtime - can access database)
  const session = await auth.api.getSession({
    headers: await headers(),
  });

  // Verify admin access
  if (!session?.user || session.user.role !== "admin") {
    redirect("/");
  }

  return <UsersPageClient />;
}

