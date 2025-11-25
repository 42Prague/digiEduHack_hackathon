import { redirect } from "next/navigation";
import { auth } from "~/server/better-auth";
import { headers } from "next/headers";
import { FormBuilder } from "./_components/FormBuilder";

export default async function FormBuilderPage({
  params,
}: {
  params: Promise<{ form_id: string }>;
}) {
  const session = await auth.api.getSession({
    headers: await headers(),
  });

  if (!session?.user || session.user.role !== "admin") {
    redirect("/");
  }

  const { form_id } = await params;

  return <FormBuilder formId={form_id} />;
}

