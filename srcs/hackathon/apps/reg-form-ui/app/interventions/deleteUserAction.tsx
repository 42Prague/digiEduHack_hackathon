"use server";

import { revalidatePath } from "next/cache";

import { envs } from "../env-loader";

export async function deleteUserAction(userId: number) {
  try {
    const res = await fetch(`http://${envs.REG_FORM_URL}/v1/users/${userId}`, {
      method: "DELETE",
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(
        `Failed to delete user: ${res.status} ${res.statusText} - ${errorText}`,
      );
    }

    revalidatePath("/users");

    return { success: true };
  } catch (error: unknown) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error occurred";
    console.error("Error in deleteUserAction:", errorMessage);
    return { success: false, error: errorMessage };
  }
}
