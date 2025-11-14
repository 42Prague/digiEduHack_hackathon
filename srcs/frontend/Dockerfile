FROM node:20-alpine
WORKDIR /app
# Install dependencies first for better caching
COPY package.json package-lock.json* ./
RUN npm install
# Copy the rest of the app
COPY . .
EXPOSE 4200
CMD ["npm", "start"]

