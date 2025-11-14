"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { createUserAction } from "./createUserAction";

import { CreateUserActionProps } from "./createUserAction";

export function CreateUserButton({
  firstName,
  lastName,
  password,
  email,
}: CreateUserActionProps) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const handleCreate = () => {
    setError(null); // Clear previous errors
    startTransition(async () => {
      const result = await createUserAction({
        firstName,
        lastName,
        password,
        email,
      });
      if (result.success) {
        console.log(`Create successful for new user`);
      } else {
        console.error(`Create failed for new user: `, result.error);
        setError(result.error || "Failed to create user.");
      }
    });
  };

  return (
    <>
      <Button
        // variant="secondary"
        onClick={handleCreate}
        disabled={isPending}
      >
        {isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            Creating...
          </>
        ) : (
          <>Submit</>
        )}
      </Button>
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}{" "}
      {/* move somewhere else */}
    </>
  );
}
