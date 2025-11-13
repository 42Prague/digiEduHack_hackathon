"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Trash2, Loader2 } from "lucide-react";
import { deleteUserAction } from "./deleteUserAction";

interface DeleteUserButtonProps {
  userId: number;
}

export function DeleteUserButton({ userId }: DeleteUserButtonProps) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const handleDelete = () => {
    setError(null); // Clear previous errors
    startTransition(async () => {
      const result = await deleteUserAction(userId);
      if (result.success) {
        console.log(`Delete successful for user ${userId}`);
      } else {
        console.error(`Delete failed for user ${userId}:`, result.error);
        setError(result.error || "Failed to delete user.");
      }
    });
  };

  return (
    <>
      <Button variant="destructive" onClick={handleDelete} disabled={isPending}>
        {isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            Deleting...
          </>
        ) : (
          <>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </>
        )}
      </Button>
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}{" "}
      {/* move somewhere else */}
    </>
  );
}
