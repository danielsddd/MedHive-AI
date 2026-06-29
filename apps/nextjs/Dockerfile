# Production image for the Next.js frontend (auth/session glue only). Multi-stage build:
# install workspace deps with pnpm, compile the standalone server bundle, then copy just the
# runtime artifacts into a slim final image. Build context is the REPO ROOT so the pnpm
# workspace (packages/types) resolves. Public NEXT_PUBLIC_* values are baked at build time.
FROM node:20-bookworm-slim AS base
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
RUN corepack enable && corepack prepare pnpm@9.12.0 --activate
WORKDIR /repo

FROM base AS deps
COPY pnpm-workspace.yaml package.json ./
COPY apps/nextjs/package.json apps/nextjs/package.json
COPY packages/types/package.json packages/types/package.json
RUN pnpm install --frozen-lockfile=false

FROM base AS build
COPY --from=deps /repo/node_modules ./node_modules
COPY --from=deps /repo/apps/nextjs/node_modules ./apps/nextjs/node_modules
COPY . .
WORKDIR /repo/apps/nextjs
RUN pnpm build

FROM node:20-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /repo/apps/nextjs/.next/standalone ./
COPY --from=build /repo/apps/nextjs/.next/static ./apps/nextjs/.next/static
COPY --from=build /repo/apps/nextjs/public ./apps/nextjs/public
EXPOSE 3000
CMD ["node", "apps/nextjs/server.js"]
