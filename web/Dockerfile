# =============================================================================
# Multi-stage Dockerfile for Next.js Web Application
# Targets: app_dev (development), app_prod (production)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: deps - Install dependencies
# This stage is cached and only rebuilds when package files change
# -----------------------------------------------------------------------------
FROM node:22-alpine AS deps

# Install libc6-compat for Alpine compatibility with some npm packages
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json ./

# Install dependencies with clean install for reproducibility
# Using --frozen-lockfile equivalent for npm
RUN npm ci

# -----------------------------------------------------------------------------
# Stage 2: builder - Build the Next.js application
# Only used for production builds
# -----------------------------------------------------------------------------
FROM node:22-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
# This creates the .next folder with the production build
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3a: app_dev - Development target
# Uses volume mounts for hot-reload, optimized for developer experience
# -----------------------------------------------------------------------------
FROM node:22-alpine AS app_dev

WORKDIR /app

# Install libc6-compat for Alpine compatibility
RUN apk add --no-cache libc6-compat

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy package files (source will be mounted as volume)
COPY package.json package-lock.json ./

# Set development environment
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Expose the development port
EXPOSE 3000

# Set hostname to allow external connections
ENV HOSTNAME="0.0.0.0"

# Development command with Turbopack for fast HMR
CMD ["npm", "run", "dev"]

# -----------------------------------------------------------------------------
# Stage 3b: app_prod - Production target
# Minimal image using Next.js standalone output
# -----------------------------------------------------------------------------
FROM node:22-alpine AS app_prod

WORKDIR /app

# Install libc6-compat for Alpine compatibility
# Install sharp dependencies for optimized image handling
RUN apk add --no-cache libc6-compat

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy the standalone build from builder stage
# The standalone folder contains a minimal Node.js server
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./

# Copy static files (required for serving static assets)
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Copy public folder (images, fonts, etc.)
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Switch to non-root user
USER nextjs

# Expose the production port
EXPOSE 3000

# Set hostname for container networking
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Production command - run the standalone server
CMD ["node", "server.js"]
