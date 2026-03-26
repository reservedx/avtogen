FROM node:20-alpine AS deps

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

FROM node:20-alpine AS builder

WORKDIR /app/frontend
COPY --from=deps /app/frontend/node_modules ./node_modules
COPY frontend /app/frontend
RUN npm run build

FROM node:20-alpine AS runner

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
WORKDIR /app/frontend

COPY --from=builder /app/frontend/.next ./.next
COPY --from=builder /app/frontend/node_modules ./node_modules
COPY --from=builder /app/frontend/package.json ./package.json

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
