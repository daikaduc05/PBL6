# Multi-stage build matching the Backend services' pattern — build-time
# deps (devDependencies, TypeScript) never ship in the runtime image.
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Real values are injected at deploy time; these let the build's static
# generation pass (frontend-ci.yml's build job uses the same placeholders).
ENV NEXT_PUBLIC_API_BASE_URL=http://localhost:8080/api/v1
ENV NEXT_PUBLIC_CDN_BASE_URL=https://cdn.example.com
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "run", "start"]
