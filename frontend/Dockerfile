FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json ./
# npm install generates the lock file on first run — no lock file needed
RUN npm install

FROM node:20-alpine AS builder
WORKDIR /app
ARG BACKEND_URL=http://backend:8000
ARG NEXT_PUBLIC_API_URL
ENV BACKEND_URL=${BACKEND_URL}
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# standalone output bundles everything needed to run
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
# public folder may not exist — create it to avoid COPY errors
RUN mkdir -p ./public
EXPOSE 3000
CMD ["node", "server.js"]
