"use server";

import { revalidatePath } from "next/cache";
import { envs } from "../env-loader";

export interface CreateUserActionProps {
  firstName: string;
  lastName: string;
  password: string;
  email: string;
}

export async function createUserAction({
  firstName,
  lastName,
  email,
  password,
}: CreateUserActionProps) {
  try {
    const res = await fetch(`http://${envs.REG_FORM_URL}/v1/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ firstName, lastName, email, password }),
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(
        `Failed to create user: ${res.status} ${res.statusText} - ${errorText}`,
      );
    }

    revalidatePath("/users");

    return { success: true };
  } catch (error: unknown) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error occurred";
    console.error("Error in createUserAction:", errorMessage);
    return { success: false, error: errorMessage };
  }
}
