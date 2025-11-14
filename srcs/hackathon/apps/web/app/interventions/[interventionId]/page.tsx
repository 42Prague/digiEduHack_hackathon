import React from "react";
import { notFound } from "next/navigation";
import InterventionsList from "@/components/interventions-list";

export default async function UserDetails({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const interventionId = (await params).userId;

  if (parseInt(interventionId) >= 1000) {
    notFound();
  }

  return (
    <div>
      <InterventionsList />
    </div>
  );
}
