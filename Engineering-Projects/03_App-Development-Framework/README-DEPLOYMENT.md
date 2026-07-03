# Deployment Guide

## Overview
This guide covers deployment strategies and configurations for different environments.

## Prerequisites

### Required Tools
- Node.js 18+
- npm/pnpm
- Git
- Docker (for containerized deployments)
- Cloud provider CLI tools (AWS CLI, Vercel CLI, etc.)

### Environment Setup
1. Clone the repository
2. Install dependencies: `npm install`
3. Set up environment variables
4. Run tests: `npm test`
5. Build the application: `npm run build`

## Environment Variables

### Production Environment
```env
# Application
NODE_ENV=production
NEXTAUTH_URL=https://your-domain.com
NEXTAUTH_SECRET=your-production-secret

# Database
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://host:port

# External Services
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASS=your-email-password

# API Keys
STRIPE_SECRET_KEY=sk_live_...
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Feature Flags
ENABLE_ANALYTICS=true
ENABLE_DEBUG=false
```

### Staging Environment
```env
# Application
NODE_ENV=staging
NEXTAUTH_URL=https://staging.your-domain.com
NEXTAUTH_SECRET=your-staging-secret

# Database
DATABASE_URL=postgresql://user:password@staging-host:port/database

# External Services (use test/sandbox versions)
STRIPE_SECRET_KEY=sk_test_...
```

## Deployment Platforms

### Vercel (Recommended for Next.js)

#### Setup
1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Link project: `vercel link`

#### Deploy
```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

#### Configuration
Create `vercel.json`:
```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "env": {
    "NODE_ENV": "production"
  },
  "functions": {
    "src/app/api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

### Railway

#### Setup
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`

#### Deploy
```bash
# Deploy
railway up

# Set environment variables
railway variables set NODE_ENV=production
railway variables set DATABASE_URL=your-database-url
```

### AWS (Full Stack)

#### Using AWS Amplify
1. Connect your GitHub repository
2. Configure build settings:
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm install
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: .next
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
      - .next/cache/**/*
```

#### Using AWS ECS with Docker
1. Create `Dockerfile`:
```dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

2. Build and push to ECR:
```bash
# Build image
docker build -t your-app .

# Tag for ECR
docker tag your-app:latest your-account.dkr.ecr.region.amazonaws.com/your-app:latest

# Push to ECR
docker push your-account.dkr.ecr.region.amazonaws.com/your-app:latest
```

### Docker Compose (Local/Development)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/app
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

Deploy:
```bash
docker-compose up -d
```

## Database Setup

### PostgreSQL
```bash
# Create database
createdb your-app-db

# Run migrations
npm run db:migrate

# Seed data (optional)
npm run db:seed
```

### MongoDB
```bash
# Connect to MongoDB
mongosh "mongodb://localhost:27017/your-app-db"

# Create collections and indexes
use your-app-db
db.users.createIndex({ email: 1 }, { unique: true })
```

## CI/CD Pipeline

### GitHub Actions
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - run: npm ci
      - run: npm run build
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
```

## Monitoring and Logging

### Health Checks
Create health check endpoint:
```typescript
// src/app/api/health/route.ts
export async function GET() {
  try {
    // Check database connection
    await db.$queryRaw`SELECT 1`;
    
    return Response.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: 'connected',
        redis: 'connected'
      }
    });
  } catch (error) {
    return Response.json(
      { status: 'unhealthy', error: error.message },
      { status: 500 }
    );
  }
}
```

### Logging
```typescript
// src/lib/logger.ts
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

export default logger;
```

## Security Considerations

### Environment Variables
- Never commit `.env` files
- Use different secrets for each environment
- Rotate secrets regularly
- Use secret management services (AWS Secrets Manager, Azure Key Vault)

### HTTPS
- Always use HTTPS in production
- Configure proper SSL certificates
- Use HSTS headers

### CORS
```typescript
// next.config.ts
const nextConfig = {
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: 'https://your-domain.com' },
          { key: 'Access-Control-Allow-Methods', value: 'GET, POST, PUT, DELETE' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization' },
        ],
      },
    ];
  },
};
```

## Performance Optimization

### Caching
```typescript
// src/lib/cache.ts
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

export const cache = {
  async get(key: string) {
    const value = await redis.get(key);
    return value ? JSON.parse(value) : null;
  },
  
  async set(key: string, value: any, ttl = 3600) {
    await redis.setex(key, ttl, JSON.stringify(value));
  },
  
  async del(key: string) {
    await redis.del(key);
  }
};
```

### CDN Configuration
- Use Cloudflare or AWS CloudFront
- Configure proper cache headers
- Optimize images and static assets

## Rollback Strategy

### Database Migrations
```bash
# Rollback last migration
npm run db:migrate:rollback

# Rollback to specific version
npm run db:migrate:rollback -- --to 20240101000000
```

### Application Rollback
```bash
# Vercel
vercel rollback

# Railway
railway rollback

# Docker
docker-compose down
docker-compose up -d --scale app=0
docker-compose up -d
```

## Troubleshooting

### Common Issues

**Build Fails**
- Check Node.js version compatibility
- Verify all dependencies are installed
- Check for TypeScript errors

**Database Connection Issues**
- Verify DATABASE_URL format
- Check network connectivity
- Ensure database is running

**Environment Variables Not Loading**
- Check variable names match exactly
- Verify .env files are in correct location
- Restart the application after changes

### Debug Mode
```bash
# Enable debug logging
DEBUG=* npm run dev

# Check application logs
npm run logs

# Database query logging
DATABASE_LOGGING=true npm run dev
```

## Support
For deployment issues:
1. Check the logs first
2. Verify environment variables
3. Test locally with production settings
4. Contact the development team
