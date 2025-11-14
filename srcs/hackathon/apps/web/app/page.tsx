"use client";

import React from "react";
import { ListChecks, School } from "lucide-react"; // Icons for clarity

// In a real Next.js environment, you would use next/link here.
// Since this is a self-contained environment, we'll use a standard anchor tag
// styled as a Card, which will still perform the navigation.

/**
 * A component representing a navigable card on the landing page.
 * @param {string} href - The destination URL.
 * @param {string} title - The main title of the card.
 * @param {string} description - The descriptive text below the title.
 * @param {React.ReactNode} icon - An icon element.
 */
const NavigationCard: React.FC<{
  href: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}> = ({ href, title, description, icon }) => (
  <a
    href={href}
    className="
      flex flex-col items-center justify-center p-8 rounded-xl
      shadow-lg transition-all duration-300 transform
      bg-card border-2 border-border
      hover:shadow-xl hover:scale-[1.02] hover:border-primary/50
      focus:outline-none focus:ring-4 focus:ring-primary/50
      w-full max-w-sm cursor-pointer
    "
    role="link"
  >
    <div className="text-primary mb-4">{icon}</div>
    <h2 className="text-2xl font-bold text-foreground mb-1">{title}</h2>
    <p className="text-center text-sm text-muted-foreground">{description}</p>
  </a>
);

export default function Home() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 sm:p-12">
      <div className="text-center mb-12">
        <h1 className="text-5xl font-extrabold text-foreground mb-3">
          Dashboard Portal
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Select a domain to manage and analyze educational data.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl">
        {/* Intervention Management Card */}
        <NavigationCard
          href="/interventions"
          title="Interventions"
          description="View, analyze, and manage all recorded program interventions and processed data."
          icon={<ListChecks className="h-10 w-10" />}
        />

        {/* School Management Card */}
        <NavigationCard
          href="/schools"
          title="Schools"
          description="Access detailed information and administrative settings for participating schools."
          icon={<School className="h-10 w-10" />}
        />
      </div>
    </div>
  );
}
