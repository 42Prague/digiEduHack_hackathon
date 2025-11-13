"use client";

import { useRouter } from "next/navigation";
import React from "react";

interface Intervention {
  id: number;
  type: string;
  students: number;
  startDate: string;
  status: "Active" | "Completed" | "Pending";
  success: number;
}

interface InterventionTableRowProps {
  intervention: Intervention;
}

export default function InterventionTableRow({
  intervention,
}: InterventionTableRowProps) {
  const router = useRouter();

  const handleRowClick = () => {
    // Navigate to the dynamic route for the specific intervention ID
    router.push(`/interventions/${intervention.id}`);
  };

  const statusClassName = {
    Active: "bg-accent/20 text-accent",
    Completed: "bg-primary/20 text-primary",
    Pending: "bg-muted text-muted-foreground",
  }[intervention.status];

  return (
    // Make the entire row clickable and apply hover styles
    <tr
      key={intervention.id}
      className="border-b border-border hover:bg-card/50 transition-colors cursor-pointer"
      onClick={handleRowClick}
    >
      <td className="px-4 py-3 text-sm text-foreground">{intervention.type}</td>
      <td className="px-4 py-3 text-sm text-foreground">
        {intervention.students}
      </td>
      <td className="px-4 py-3 text-sm text-muted-foreground">
        {new Date(intervention.startDate).toLocaleDateString()}
      </td>
      <td className="px-4 py-3 text-sm">
        <span
          className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${statusClassName}`}
        >
          {intervention.status}
        </span>
      </td>
      <td className="px-4 py-3 text-sm font-medium text-foreground">
        {intervention.success}%
      </td>
    </tr>
  );
}
