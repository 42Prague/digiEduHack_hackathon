FROM node:lts-alpine AS builder
RUN apk add --no-cache libc6-compat openssl

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy the entire monorepo (needed for workspace dependencies)
COPY . .

# Install all workspace dependencies
RUN pnpm install

# Build the application 
RUN SKIP_ENV_VALIDATION=0 SKIP_MIGRATIONS=true pnpm build

##### RUNNER

FROM gcr.io/distroless/nodejs20-debian12 AS runner
WORKDIR /app

ENV NODE_ENV=production

# Copy standalone output (includes server.js and node_modules)
COPY --from=builder /app/.next/standalone ./

# Copy static files
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Copy drizzle migration files
COPY --from=builder /app/drizzle ./drizzle

EXPOSE 3000
ENV PORT=3000

CMD ["server.js"]
