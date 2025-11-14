import { createAuthClient } from "better-auth/react";
import { adminClient } from "better-auth/client/plugins"

export const authClient = createAuthClient({
    plugins: [
        adminClient()
    ]
});

export type Session = typeof authClient.$Infer.Session;
