// app/page.tsx
import { UserList } from "./userList";
import { LoginCard } from "./loginCard";
import React from "react";
import InterventionsList from "@/components/interventions-list";

export default async function Home() {
  return (
    <div>
      <InterventionsList />
    </div>
  );
}
