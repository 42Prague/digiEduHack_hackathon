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


COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/public ./srcs/eduforms/public
COPY --from=builder /app/package.json ./package.json

# Add this line to copy the drizzle migration files
COPY --from=builder /app/drizzle ./srcs/eduforms/drizzle

# COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/.next/static ./srcs/eduforms/.next/static



EXPOSE 3000
ENV PORT=3000

CMD ["server.js"]
