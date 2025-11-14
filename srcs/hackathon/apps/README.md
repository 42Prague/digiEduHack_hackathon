# Adding a New Application to the Monorepo

This guide outlines the standard procedure for adding a new application (e.g., a web server, a documentation site) to this pnpm monorepo. Following these steps ensures consistency and leverages the power of pnpm workspaces correctly.

_Last updated: July 2025_

---

## Core Principles

Our monorepo operates on a simple but important principle:

1. **Package Definition**: Every app or package within the `/apps` or `/packages` directory must have its own `package.json` file. This file defines its name, scripts, and dependencies.
2. **Centralized Installation**: While each app defines its own dependencies, `pnpm` installs all packages into a single, shared `node_modules` directory at the root of the monorepo.
3. **Targeted Commands**: We always run commands from the **monorepo root**, using the `--filter` flag to target specific apps.

---

## Step-by-Step Guide

Here is the standard workflow for creating a new application called `my-new-app`.

### 1. Create the App Directory

Navigate to the `apps` directory and create a new folder for your application.

```bash
cd apps
mkdir my-new-app
cd my-new-app
```

### 2. Initialize the Package

Inside the new directory, initialize a `package.json` file. This officially registers it as a package within the workspace.

```bash
# You are now inside ./apps/my-new-app
pnpm init
```

This will create a basic `package.json`. You can edit the details later.

### 3. Add Dependencies

Return to the monorepo root to add dependencies. Use the `--filter` flag to specify that the dependency is for `my-new-app`.

```bash
# Navigate back to the monorepo root
cd ../..

# Add a production dependency (e.g., fastify)
pnpm --filter my-new-app add fastify

# Add development dependencies (e.g., typescript)
pnpm --filter my-new-app add -D typescript @types/node tsx
```

This will add the dependencies to `/apps/my-new-app/package.json`, not the root `package.json`.

### 4. Add a Development Script

Open `/apps/my-new-app/package.json` and add a `dev` script to run your application.

```json
{
  "name": "my-new-app",
  // ... other fields
  "scripts": {
    "dev": "tsx watch src/index.ts"
  }
  // ... other fields
}
```

### 5. Run Your Application

From the monorepo root, run your app's dev script.

```bash
pnpm --filter my-new-app dev
```

Your new application is now running!

---

## Important Concepts: FAQ

### How do I decide where to install a package?

- For a specific app (e.g., fastify, react): Use `--filter`. This is for dependencies an application needs to run.

```bash
pnpm --filter <app-name> add <package-name>
```

- For the entire monorepo (dev tools like prettier, eslint): Use `-w` or `--workspace-root`.

```bash
pnpm add -D -w <package-name>
```

### Why must I run `pnpm init` first?

The `pnpm --filter <app-name>` command works by finding a package in the workspace whose `name` field in `package.json` matches `<app-name>`.  
Without a `package.json` file, `pnpm` doesn't know the package exists, so the filter will fail.

---

## Quick Reference / TL;DR

To add a new app named `my-cool-app`:

```bash
# 1. Create directory and package.json
mkdir apps/my-cool-app
cd apps/my-cool-app
pnpm init
cd ../..

# 2. Add dependencies from the root
pnpm --filter my-cool-app add <dependency>

# 3. Add dev script to apps/my-cool-app/package.json
# "dev": "..."

# 4. Run from the root
pnpm --filter my-cool-app dev
```
