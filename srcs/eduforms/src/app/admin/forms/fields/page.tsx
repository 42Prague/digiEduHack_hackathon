import { redirect } from "next/navigation";
import { auth } from "~/server/better-auth";
import { headers } from "next/headers";
import { FieldsManager } from "./_components/FieldsManager";

export default async function FieldsPage() {
  const session = await auth.api.getSession({
    headers: await headers(),
  });

  if (!session?.user || session.user.role !== "admin") {
    redirect("/");
  }

  return <FieldsManager />;
}
