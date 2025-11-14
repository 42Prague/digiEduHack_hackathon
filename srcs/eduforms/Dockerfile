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

COPY --from=builder srcs/eduforms/next.config.js ./
COPY --from=builder srcs/eduforms/public ./public
COPY --from=builder srcs/eduforms/public ./apps/webapp/public
COPY --from=builder srcs/eduforms/package.json ./package.json

# Add this line to copy the drizzle migration files
COPY --from=builder srcs/eduforms/drizzle ./apps/webapp/drizzle

COPY --from=builder srcs/eduforms/.next/standalone ./
COPY --from=builder srcs/eduforms/.next/static ./.next/static
COPY --from=builder srcs/eduforms/.next/static ./apps/webapp/.next/static

EXPOSE 3000
ENV PORT=3000

CMD ["apps/webapp/server.js"]
