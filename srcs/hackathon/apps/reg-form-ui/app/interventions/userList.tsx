// app/components/userList.tsx
"use server";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DeleteUserButton } from "./deleteUserButton";
import { ViewUserButton } from "./viewUserButton";

import { envs } from "../env-loader";

interface User {
  firstName: string;
  lastName: string;
  email: string;
  id: number;
  password: string;
}

async function getUsers(): Promise<User[]> {
  const result = await fetch(`http://${envs.REG_FORM_URL}/v1/users`, {
    cache: "no-store",
  }); // Use no-store to ensure freshness

  if (!result.ok) {
    throw new Error("Failed to fetch users");
  }

  const jsonResponse = await result.json();
  return jsonResponse.data;
}

export async function UserList() {
  let users: User[] = [];
  let error: string | null = null;

  try {
    users = await getUsers();
  } catch (e: unknown) {
    error = e instanceof Error ? e.message : "An unknown error occurred";
  }

  if (error) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24">
        <h1 className="text-red-600">
          Ooops, something went wrong. Please try again later.
        </h1>
      </main>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
        {users.length > 0 ? (
          users.map((user) => (
            <Card key={user.id} className="">
              <CardHeader className={"flex-row gap-4 items-center"}>
                <CardTitle>
                  {user.firstName} {user.lastName}
                </CardTitle>
                <CardDescription>ID: {user.id}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{user.email}</p>
              </CardContent>
              <CardFooter className="flex justify-between">
                <ViewUserButton userId={user.id} />
                <DeleteUserButton userId={user.id} />
              </CardFooter>
            </Card>
          ))
        ) : (
          <p className="text-center col-span-full text-muted-foreground">
            No users found.
          </p>
        )}
      </div>
    </>
  );
}
