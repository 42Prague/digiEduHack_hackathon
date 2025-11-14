// components/JobDetailDashboard.tsx
"use client";

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { Check, Cpu, Briefcase, DollarSign, MapPin, Zap } from "lucide-react";
import { mockJobData } from "@/lib/data"; // Replace with actual data fetching

// Helper function to capitalize strings
const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export function JobDetailDashboard() {
  const job = mockJobData;
  const insights = job.analyticalInsights;

  return (
    <div className="space-y-6 p-8 max-w-6xl mx-auto">
      {/* Header and Core Details */}
      <header className="border-b pb-4">
        <h1 className="text-3xl font-bold">{job.originalAdData.jobTitle}</h1>
        <p className="text-xl text-muted-foreground">
          {job.originalAdData.companyName}
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge variant="default" className="bg-green-600 hover:bg-green-700">
            {insights.corePositionDetails.seniorityLevel}
          </Badge>
          <Badge variant="outline">
            <MapPin className="h-3 w-3 mr-1" />
            {insights.locationAndWorkModel.locationCity}
          </Badge>
          <Badge variant="outline">
            {insights.locationAndWorkModel.workModel}
          </Badge>
          <Badge variant="secondary">
            {insights.corePositionDetails.industryVertical}
          </Badge>
        </div>
      </header>

      {/* Main Content Grid */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Salary Card */}
        <Card className="md:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <DollarSign className="h-4 w-4 mr-2" /> Compensation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {insights.compensationAndFinancials.salaryMin.toLocaleString()} –{" "}
              {insights.compensationAndFinancials.salaryMax.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {insights.compensationAndFinancials.salaryCurrency} /{" "}
              {insights.compensationAndFinancials.salaryPeriod}
            </p>
          </CardContent>
        </Card>

        {/* Benefits Card */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Briefcase className="h-4 w-4 mr-2" /> Key Benefits
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-y-2 text-sm">
            <div className="flex items-center">
              <Check className="h-4 w-4 text-green-500 mr-2" />{" "}
              {insights.benefitsAndPerks.paidVacationDays} Days Vacation
            </div>
            <div className="flex items-center">
              {insights.benefitsAndPerks.sickDays ? (
                <Check className="h-4 w-4 text-green-500 mr-2" />
              ) : (
                "✗"
              )}{" "}
              Sick Days
            </div>
            {insights.benefitsAndPerks.hardwareProvided.map((item) => (
              <div key={item} className="flex items-center">
                <Cpu className="h-4 w-4 text-blue-500 mr-2" /> {item} Provided
              </div>
            ))}
            {insights.benefitsAndPerks.wellnessBenefits.map((item) => (
              <div key={item} className="flex items-center">
                <Zap className="h-4 w-4 text-yellow-500 mr-2" /> {item}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Technical Stack Card */}
        <Card className="md:col-span-3">
          <CardHeader>
            <CardTitle>Technical Requirements</CardTitle>
            <CardDescription>
              {insights.corePositionDetails.jobFunction} Focus
            </CardDescription>
          </CardHeader>
          <CardContent>
            <h4 className="text-md font-semibold mb-2">Core Tech Stack</h4>
            <div className="flex flex-wrap gap-2 mb-4">
              {insights.technicalSkillsAndMethodologies.coreTechStack.map(
                (skill) => (
                  <Badge key={skill} className="bg-blue-600 hover:bg-blue-700">
                    {skill}
                  </Badge>
                ),
              )}
            </div>
            <h4 className="text-md font-semibold mb-2">
              Preferred/Bonus Skills
            </h4>
            <div className="flex flex-wrap gap-2">
              {insights.technicalSkillsAndMethodologies.preferredTechStack.map(
                (skill) => (
                  <Badge key={skill} variant="secondary">
                    {skill}
                  </Badge>
                ),
              )}
            </div>
          </CardContent>
        </Card>

        {/* Cultural/Work Environment Card */}
        <Card className="md:col-span-3">
          <CardHeader>
            <CardTitle>Culture & Work Environment</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableBody>
                <TableRow>
                  <TableCell className="font-medium">
                    Culture Archetype
                  </TableCell>
                  <TableCell>
                    {
                      insights.culturalAndPsychologicalIndicators
                        .companyCultureArchetype
                    }
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Team Size</TableCell>
                  <TableCell>
                    {insights.companyAndTeamContext.teamSize}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Autonomy Level</TableCell>
                  <TableCell className="flex items-center">
                    {insights.culturalAndPsychologicalIndicators.autonomyLevel}
                    {/* Simple visualization for autonomy */}
                    <Progress value={60} className="w-1/3 ml-4" />
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Full Description */}
        <Card className="md:col-span-3">
          <CardHeader>
            <CardTitle>Full Job Description</CardTitle>
          </CardHeader>
          <CardContent>
            {/* WARNING: In a real app, sanitize and format this raw HTML/text */}
            <div
              className="prose max-w-none"
              dangerouslySetInnerHTML={{
                __html: job.originalAdData.jobDescription,
              }}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
