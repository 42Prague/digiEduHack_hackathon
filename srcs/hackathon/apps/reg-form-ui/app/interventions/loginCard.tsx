"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CreateUserButton } from "./createUserButton";

export function LoginCard() {
  // State to manage form inputss
  const [formData, setFormData] = useState({
    email: "",
    firstName: "",
    lastName: "",
    password: "",
  });

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [id]: value,
    }));
  };

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Submit your info</CardTitle>
        <CardDescription>Enter your details below.</CardDescription>
      </CardHeader>
      <CardContent>
        <form>
          <div className="flex flex-col gap-4">
            <div className="grid gap-1">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                value={formData.email}
                onChange={handleInputChange}
                required
              />
            </div>
            <div className="grid gap-1">
              <Label htmlFor="firstName">First Name</Label>
              <Input
                id="firstName"
                type="text" // Changed to "text" (no "firstName" type exists)
                placeholder="John"
                value={formData.firstName}
                onChange={handleInputChange}
                required
              />
            </div>
            <div className="grid gap-1">
              <Label htmlFor="lastName">Last Name</Label>
              <Input
                id="lastName"
                type="text" // Changed to "text" (no "lastName" type exists)
                placeholder="Smith"
                value={formData.lastName}
                onChange={handleInputChange}
                required
              />
            </div>
            <div className="grid gap-1">
              <div className="flex items-center">
                <Label htmlFor="password">Password</Label>
              </div>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={handleInputChange}
                required
              />
            </div>
          </div>
        </form>
      </CardContent>
      <CardFooter className="flex-col">
        <CreateUserButton
          email={formData.email}
          firstName={formData.firstName}
          lastName={formData.lastName}
          password={formData.password}
        />
      </CardFooter>
    </Card>
  );
}
