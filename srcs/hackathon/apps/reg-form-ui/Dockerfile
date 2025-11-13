# syntax=docker/dockerfile:1.4

# ==============================================================================
# STAGE 1: base
# Establishes the core environment with Node.js, pnpm, and Turbo.
# ==============================================================================
FROM node:20-alpine AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN apk add --no-cache libc6-compat && corepack enable
# PREPARE PNPM: Install the exact pnpm version to prevent Corepack's download prompt
RUN corepack prepare pnpm@10.13.1 --activate

# ==============================================================================
# STAGE 2: pruner
# Creates a pruned, partial monorepo for the target application.
# ==============================================================================
FROM base AS pruner
WORKDIR /app
RUN pnpm add --global turbo
COPY . .
ARG APP_NAME
RUN turbo prune --scope=${APP_NAME} --docker

# ==============================================================================
# STAGE 3: installer
# Installs all dependencies (dev and prod) in a dedicated layer.
# ==============================================================================
FROM base AS installer
WORKDIR /app
COPY --from=pruner /app/out/json/ .
COPY --from=pruner /app/out/pnpm-lock.yaml .
COPY --from=pruner /app/out/pnpm-workspace.yaml .
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile --ignore-scripts

# ==============================================================================
# STAGE 4: builder
# Builds the application source code using the full dependencies.
# ==============================================================================
FROM installer AS builder
WORKDIR /app
ARG APP_NAME
COPY --from=pruner /app/out/full/ .
#RUN pnpm run db:generate --filter ${APP_NAME}
RUN pnpm run build --filter ${APP_NAME}

# ==============================================================================
# STAGE 5: runner (Final Production Image)
# Creates the final, lean image with only built code and prod dependencies.
# ==============================================================================
FROM base AS prod
WORKDIR /app
ARG APP_NAME
RUN apk update && apk add curl
# Create a dedicated, non-root user for security.
RUN addgroup --system --gid 1001 nextjs
RUN adduser --system --uid 1001 nextjs

# Copy package manifests and workspace config from the pruner stage.
COPY --from=pruner --chown=nodejs:nodejs /app/out/json/ .
COPY --from=pruner --chown=nodejs:nodejs /app/out/pnpm-lock.yaml .
COPY --from=pruner --chown=nodejs:nodejs /app/out/pnpm-workspace.yaml .
# Install ONLY production dependencies.
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --prod --frozen-lockfile --ignore-scripts
# Copy the built application code from the builder stage and all related packages
COPY --from=builder --chown=nodejs:nodejs /app/packages ./packages
COPY --from=builder --chown=nextjs:nextjs /app/apps/${APP_NAME}/.next/standalone/apps/${APP_NAME}/ ./apps/${APP_NAME}/
COPY --from=builder --chown=nextjs:nextjs /app/apps/${APP_NAME}/.next/static ./apps/${APP_NAME}/.next/static
COPY --from=builder --chown=nextjs:nextjs /app/apps/${APP_NAME}/public ./apps/${APP_NAME}/
# Activate the new user created above
USER nextjs
ENV NODE_ENV production
EXPOSE 3000
# Define the command to start the application.
WORKDIR /app/apps/${APP_NAME}
CMD ["node", "./server.js"]

# ==============================================================================
# STAGE 6: dev (Development Image)
# Creates a development-ready image. This stage remains unchanged.
# ==============================================================================
FROM installer AS dev
WORKDIR /app
ARG APP_NAME
COPY --from=pruner /app/out/full/ .
#RUN pnpm run db:generate --filter ${APP_NAME}
RUN pnpm run build --filter=${APP_NAME}^...
# No need to start the process here, better from docker compose file in command key to start dev script
#CMD ["pnpm", "--filter", "${APP_NAME}", "run", "start"]