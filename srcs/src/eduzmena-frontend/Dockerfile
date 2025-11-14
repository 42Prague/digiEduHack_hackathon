FROM node:20-alpine AS base

WORKDIR /app

# Install only prod dependencies (live-server)
COPY package*.json ./
RUN npm install --omit=dev

# Copy static assets
COPY . .

ENV PORT=4173
EXPOSE 4173

CMD ["npm", "run", "start"]

