# Monorepo Packages

The primary goal of this structure is to promote code reuse, maintain consistency across our projects, and improve developer velocity. By creating shared packages, we adhere to the **Don't Repeat Yourself (DRY)** principle and establish a single source of truth for common functionality.

---

## Our Packages

Here is a list of the shared packages currently available in this monorepo:

| Package Directory    | npm Name                  | Description                                                                           |
| -------------------- | ------------------------- | ------------------------------------------------------------------------------------- |
| `ui/`                | `@repo/ui`                | A library of shared React components (Buttons, Cards, etc.) for a consistent UI.      |
| `utils/`             | `@repo/utils`             | Common, stateless helper functions (e.g., date formatters, validators).               |
| `types/`             | `@repo/types`             | Shared TypeScript types, interfaces, and schemas (e.g., API contracts).               |
| `eslint-config/`     | `@repo/eslint-config`     | The base ESLint configuration to enforce consistent code style and quality.           |
| `typescript-config/` | `@repo/typescript-config` | Shared `tsconfig.json` files that other packages and apps should extend.              |
| `testing-utils/`     | `@repo/testing-utils`     | Reusable utilities for testing, such as custom render functions, mocks, and fixtures. |
| `scripts/`           | `@repo/scripts`           | Reusable automation scripts for tasks like database seeding or deployment.            |

---

## Consuming Packages

All internal packages can be consumed by other packages or applications within this monorepo using the **workspace protocol**. This tells the package manager (npm/Yarn/pnpm) to use the local code from the `packages/` directory instead of fetching it from a remote registry.

### To use a shared package:

1. Navigate to the `package.json` of the application or package where you want to use it (e.g., `apps/web/package.json`).
2. Add the shared package to your `dependencies` or `devDependencies`, using the version `workspace:*`.

**Example**: Using the `@repo/ui` and `@repo/utils` packages in a web app.

```json
// apps/web/package.json
{
  "name": "web",
  "version": "1.0.0",
  "dependencies": {
    "react": "18.2.0",
    "@repo/ui": "workspace:*",
    "@repo/utils": "workspace:*"
  },
  "devDependencies": {
    "@repo/eslint-config": "workspace:*"
  }
}
```

After updating `package.json`, run `pnpm install` (or your package manager's install command) from the root of the monorepo. This will create the necessary symlinks in your `node_modules` directory.

### Example Usage

```tsx
// In a component within apps/web
import { Button } from "@repo/ui";
import { formatDate } from "@repo/utils";

export function MyComponent() {
  return (
    <div>
      <p>Today is: {formatDate(new Date())}</p>
      <Button onClick={() => alert("Clicked!")}>Click Me</Button>
    </div>
  );
}
```

---

## Creating a New Package

### 1. Create the Directory

Create a new folder inside `packages/` with a descriptive, kebab-case name (e.g., `api-client`).

### 2. Initialize `package.json`

```json
// packages/api-client/package.json
{
  "name": "@repo/api-client",
  "version": "1.0.0",
  "private": true,
  "main": "./dist/index.js",
  "module": "./dist/index.mjs",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "scripts": {
    "build": "tsup src/index.ts --format cjs,esm --dts",
    "dev": "tsup src/index.ts --format cjs,esm --dts --watch",
    "lint": "eslint . --max-warnings 0"
  },
  "devDependencies": {
    "@repo/eslint-config": "workspace:*",
    "@repo/typescript-config": "workspace:*",
    "eslint": "^8.57.0",
    "tsup": "^8.0.2",
    "typescript": "^5.3.3"
  }
}
```

**Notes**:

- `name`: Must be unique and scoped with `@repo/`.
- `main`, `module`, `types`: Entry points for different module systems.
- `exports`: Defines public API and supports modern bundlers.
- `scripts`: Uses `tsup` for bundling.

### 3. Add a `tsconfig.json`

```json
// packages/api-client/tsconfig.json
{
  "extends": "@repo/typescript-config/base.json",
  "include": ["src"],
  "exclude": ["dist", "build", "node_modules"]
}
```

### 4. Write Your Code

Create an `src/` directory and start coding.

---

## Package API Design (Exporting)

Export strategy significantly affects bundle size and tree-shaking. We use two main strategies:

### 1. Barrel File Strategy (for `types`, `utils`)

Good for packages where consumers likely import multiple items.

#### Structure

```
packages/types/
├── src/
│   ├── user.ts       // export interface User { ... }
│   ├── product.ts    // export interface Product { ... }
│   └── index.ts      // Barrel file
└── package.json
```

**Barrel File (`src/index.ts`)**:

```ts
export * from "./user";
export * from "./product";
```

**package.json `exports`**:

```json
{
  "name": "@repo/types",
  "exports": {
    ".": "./src/index.ts"
  }
}
```

**Consumption**:

```ts
import { User, Product } from "@repo/types";
```

---

### 2. Granular Exports Strategy (for `ui`)

Optimized for tree-shaking in component libraries.

#### Structure

```
packages/ui/
├── src/
│   ├── Button.tsx
│   ├── Card.tsx
│   └── index.tsx     // Optional barrel
└── package.json
```

**package.json `exports`**:

```json
{
  "name": "@repo/ui",
  "exports": {
    ".": "./src/index.tsx",
    "./Button": "./src/Button.tsx",
    "./Card": "./src/Card.tsx"
  }
}
```

- `.` — main entry (`@repo/ui`)
- `./Button` — deep import (`@repo/ui/Button`)

**Recommended Usage**:

```tsx
import { Button } from "@repo/ui/Button";
import { Card } from "@repo/ui/Card";
```

This ensures only necessary code is bundled.

---
