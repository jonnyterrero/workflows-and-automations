# Tech Stack Documentation

## Overview
This document outlines the standard technology stack and best practices used across our projects.

## Core Technologies

### Web Frontend
- **Framework**: React with Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: React Context API / Zustand
- **Forms**: React Hook Form + Zod validation
- **Icons**: Lucide React

### Mobile App
- **Framework**: Flutter
- **Language**: Dart
- **State Management**: Provider / Riverpod / Bloc
- **UI Components**: Material Design / Cupertino
- **Navigation**: GoRouter
- **HTTP Client**: Dio / http package
- **Local Storage**: SharedPreferences / Hive

### Backend
- **Runtime**: Node.js 18+
- **Framework**: Express.js
- **Language**: TypeScript / JavaScript
- **Database**: PostgreSQL
- **ORM**: Prisma / TypeORM
- **Authentication**: JWT / Passport.js
- **API**: RESTful APIs
- **Validation**: Joi / Zod

### Database
- **Primary Database**: PostgreSQL
- **ORM**: Prisma (preferred) / TypeORM
- **Migrations**: Prisma Migrate / TypeORM CLI
- **Connection Pooling**: PgBouncer
- **Backup**: Automated PostgreSQL backups

### Cloud Platforms
- **Primary**: AWS (Amazon Web Services)
- **Secondary**: Google Cloud Platform (GCP)
- **Container Orchestration**: AWS ECS / Google Cloud Run
- **Serverless**: AWS Lambda / Google Cloud Functions
- **Storage**: AWS S3 / Google Cloud Storage
- **CDN**: AWS CloudFront / Google Cloud CDN

### Development Tools
- **Package Manager**: npm / pnpm
- **Linting**: ESLint + Prettier
- **Type Checking**: TypeScript
- **Testing**: Jest + React Testing Library (Web), Flutter Test (Mobile)
- **Version Control**: Git + GitHub
- **CI/CD**: GitHub Actions
- **Mobile Development**: Android Studio / VS Code with Flutter extensions

## Project Structure

### Web Frontend (Next.js)
```
web-frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   ├── components/          # Reusable components
│   │   └── ui/             # shadcn/ui components
│   ├── lib/                # Utilities and configurations
│   ├── hooks/              # Custom React hooks
│   └── types/              # TypeScript type definitions
├── public/                 # Static assets
├── docs/                   # Documentation
└── tests/                  # Test files
```

### Mobile App (Flutter)
```
mobile-app/
├── lib/
│   ├── main.dart           # App entry point
│   ├── models/             # Data models
│   ├── services/           # API services
│   ├── providers/          # State management
│   ├── screens/            # UI screens
│   ├── widgets/            # Reusable widgets
│   └── utils/              # Utility functions
├── test/                   # Unit tests
├── integration_test/       # Integration tests
└── assets/                 # Images, fonts, etc.
```

### Backend (Express.js)
```
backend/
├── src/
│   ├── controllers/        # Route controllers
│   ├── models/             # Database models
│   ├── routes/             # API routes
│   ├── middleware/         # Custom middleware
│   ├── services/           # Business logic
│   ├── utils/              # Utility functions
│   └── types/              # TypeScript definitions
├── prisma/                 # Database schema and migrations
├── tests/                  # Test files
└── docs/                   # API documentation
```

### Full-Stack Project Structure
```
full-stack-project/
├── web-frontend/           # Next.js React app
├── mobile-app/             # Flutter mobile app
├── backend/                # Express.js API
├── shared/                 # Shared types and utilities
├── docs/                   # Project documentation
├── docker-compose.yml      # Local development setup
└── README.md               # Project overview
```

## Coding Standards

### TypeScript (Web & Backend)
- Use strict mode
- Define interfaces for all data structures
- Use type guards for runtime type checking
- Prefer `interface` over `type` for object shapes
- Use proper error handling with try-catch blocks

### React (Web Frontend)
- Use functional components with hooks
- Implement proper error boundaries
- Use React.memo for performance optimization
- Follow the single responsibility principle
- Use TypeScript for all components

### Flutter (Mobile)
- Follow Dart style guide
- Use proper widget composition
- Implement proper state management patterns
- Use const constructors where possible
- Follow Material Design guidelines

### Express.js (Backend)
- Use async/await for asynchronous operations
- Implement proper error handling middleware
- Use TypeScript for type safety
- Follow RESTful API conventions
- Implement proper input validation

### CSS/Styling (Web)
- Use Tailwind CSS utility classes
- Create custom components with shadcn/ui
- Follow mobile-first responsive design
- Use CSS variables for theming

## Best Practices

### Code Organization
- Keep components small and focused
- Use barrel exports for clean imports
- Implement proper error handling
- Write meaningful commit messages
- Separate concerns between frontend, backend, and mobile

### Performance
- **Web**: Implement code splitting and dynamic imports
- **Mobile**: Use lazy loading and efficient widget trees
- **Backend**: Implement proper caching and database optimization
- **Database**: Use proper indexing and query optimization

### Security
- Validate all inputs on both frontend and backend
- Use environment variables for secrets
- Implement proper authentication (JWT)
- Follow OWASP security guidelines
- Use HTTPS in production
- Implement proper CORS policies

### Database (PostgreSQL)
- Use proper indexing strategies
- Implement connection pooling
- Use transactions for data consistency
- Regular backups and monitoring
- Use prepared statements to prevent SQL injection

## Getting Started

### Prerequisites
- **Node.js 18+** (for web frontend and backend)
- **Flutter SDK** (for mobile development)
- **PostgreSQL** (for database)
- **npm/pnpm** (package manager)
- **Git** (version control)
- **Docker** (optional, for containerized development)

### Web Frontend Setup
```bash
# Clone the repository
git clone <repository-url>
cd <project-name>/web-frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local

# Run development server
npm run dev
```

### Mobile App Setup
```bash
# Navigate to mobile app directory
cd <project-name>/mobile-app

# Get Flutter dependencies
flutter pub get

# Run on connected device/emulator
flutter run
```

### Backend Setup
```bash
# Navigate to backend directory
cd <project-name>/backend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env

# Run database migrations
npm run db:migrate

# Start development server
npm run dev
```

### Environment Variables

#### Web Frontend (.env.local)
```env
# API Configuration
NEXT_PUBLIC_API_URL="http://localhost:5000/api"
NEXT_PUBLIC_APP_URL="http://localhost:3000"

# Authentication
NEXTAUTH_SECRET="your-secret"
NEXTAUTH_URL="http://localhost:3000"
```

#### Backend (.env)
```env
# Database
DATABASE_URL="postgresql://username:password@localhost:5432/database_name"

# Server Configuration
PORT=5000
NODE_ENV="development"

# Authentication
JWT_SECRET="your-jwt-secret"
JWT_EXPIRES_IN="7d"

# External APIs
API_KEY="your-api-key"
```

#### Mobile App (config.dart)
```dart
class Config {
  static const String apiBaseUrl = 'http://localhost:5000/api';
  static const String appName = 'Your App Name';
  static const String version = '1.0.0';
}
```

## Scripts

### Web Frontend (package.json)
```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "test": "jest",
  "test:watch": "jest --watch",
  "type-check": "tsc --noEmit"
}
```

### Backend (package.json)
```json
{
  "dev": "nodemon src/index.ts",
  "build": "tsc",
  "start": "node dist/index.js",
  "lint": "eslint src/**/*.ts",
  "test": "jest",
  "test:watch": "jest --watch",
  "db:migrate": "prisma migrate dev",
  "db:generate": "prisma generate",
  "db:studio": "prisma studio"
}
```

### Mobile App (pubspec.yaml)
```yaml
# Flutter commands
flutter pub get          # Install dependencies
flutter run              # Run on connected device
flutter build apk        # Build Android APK
flutter build ios        # Build iOS app
flutter test             # Run tests
flutter analyze          # Analyze code
```

## Resources

### Web Frontend
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

### Mobile Development
- [Flutter Documentation](https://docs.flutter.dev/)
- [Dart Language Guide](https://dart.dev/guides/language)
- [Material Design](https://material.io/design)
- [Flutter Widget Catalog](https://docs.flutter.dev/development/ui/widgets)

### Backend Development
- [Express.js Documentation](https://expressjs.com/)
- [Node.js Documentation](https://nodejs.org/docs/)
- [Prisma Documentation](https://www.prisma.io/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Cloud Platforms
- [AWS Documentation](https://docs.aws.amazon.com/)
- [Google Cloud Documentation](https://cloud.google.com/docs)
- [AWS ECS Guide](https://docs.aws.amazon.com/ecs/)
- [Google Cloud Run](https://cloud.google.com/run/docs)

### Development Tools
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [ESLint Configuration](https://eslint.org/docs/user-guide/configuring/)

## Support
For questions or issues, please refer to the project-specific README or contact the development team.

## Architecture Overview

### Full-Stack Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Mobile App    │    │    Backend      │
│   (Next.js)     │    │   (Flutter)     │    │  (Express.js)   │
│                 │    │                 │    │                 │
│  - React        │    │  - Dart         │    │  - Node.js      │
│  - TypeScript   │    │  - Material UI  │    │  - TypeScript   │
│  - Tailwind CSS │    │  - State Mgmt   │    │  - REST APIs    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      PostgreSQL           │
                    │      Database             │
                    │                          │
                    │  - Data Storage          │
                    │  - Prisma ORM            │
                    │  - Migrations            │
                    └──────────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │    Cloud Platforms        │
                    │                          │
                    │  - AWS (Primary)         │
                    │  - Google Cloud (GCP)    │
                    │  - Container Deployment  │
                    │  - Serverless Functions  │
                    └──────────────────────────┘
```
