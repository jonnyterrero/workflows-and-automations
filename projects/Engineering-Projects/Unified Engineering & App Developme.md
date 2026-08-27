# 🔥 Unified Engineering & App Development Stack

**A complete, production-grade ecosystem for engineering workflows, full-stack app development, and domain systems like GlucoLoop, HeartWire, HealthHelper, and JonnyJr.**

> Built by **Jonny Terrero** — Biomedical Engineering × Software Engineering × Systems Design

---

## 🧭 Overview

This monorepo combines:

- 🧪 **Engineering Tech Stack**  
  MATLAB, Python, SQL, C/C++, simulation, CAD/FEA, data pipelines.

- 🖥 **App Development Framework**  
  Next.js, React, TypeScript, Flutter, SQL, Firebase/Supabase.

- ☁️ **DevOps & Cloud**  
  Docker, GitHub Actions, AWS/GCP deployment patterns.

- 🩺 **Domain Systems**  
  GlucoLoop (glucose analytics), HeartWire (central hub), HealthHelper (health tracking), JonnyJr (AI super-agent).

The goal: one cohesive repo that can support everything from **research prototypes** to **production apps** and **AI-assisted workflows**.

---

## 📚 Table of Contents

- [Architecture](#architecture)
- [Stacks](#stacks)
  - [Engineering Stack](#engineering-stack)
  - [App Development Stack](#app-development-stack)
  - [Domain Systems](#domain-systems)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [CI/CD & DevOps](#cicd--devops)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## 🧱 Architecture

> Diagram file: `./docs/diagrams/unified_architecture.png`  
> (Embed in GitHub with: `![Unified Architecture](./docs/diagrams/unified_architecture.png)`)

At a high level:

- The **Engineering Stack** handles numerical methods, modeling, simulation, and analysis.
- The **App Development Stack** turns those capabilities into web and mobile products.
- The **DevOps Layer** makes everything reproducible, testable, and deployable.
- **Domain Systems** (GlucoLoop, HeartWire, HealthHelper, JonnyJr) sit on top and orchestrate the ecosystem.

---

## 🧩 Stacks

### 🧪 Engineering Stack

Located in [`./engineering`](./engineering).

This is the core **Engineering Tech Stack** with two modes.

#### 01 — Comprehensive Stack (`engineering/01_comprehensive`)

The "full lab" setup.

- **Languages**: MATLAB, Python, R, C/C++, SQL  
- **CAD / Electronics**:
  - SolidWorks / OnShape / Fusion 360
  - KiCad (PCB design)
- **Simulation / FEA**:
  - COMSOL Multiphysics
  - ANSYS (CFD + Structural)
  - Simulink
  - LabVIEW
- **Use Cases**:
  - Multiphysics simulation
  - Biomedical & mechanical modeling
  - Control systems
  - Research-grade scientific computing

Best for **research, multi-disciplinary work, and heavy simulation**.

#### 02 — Optimized Stack (`engineering/02_optimized`)

The "lean and fast" setup built around **MATLAB + Python + SQL + C/C++**.

- MATLAB for modeling & numerical analysis
- Python for data pipelines, automation, ML, APIs
- SQL for storage and analytics
- C/C++ for embedded/firmware and performance-critical code
- Optional FastAPI bridge into the app stack

Best for **engineering apps, startups, and quick iteration**.

Shared utilities (datasets, notebooks, helpers) live in `engineering/shared`.

---

### 🖥 App Development Stack

Located in [`./apps`](./apps).

This is the **App Development Framework** for web, mobile, and backend services.

#### Web Frontend — `apps/web-frontend`

- Next.js 14+
- React
- TypeScript
- Tailwind CSS
- shadcn/ui

Use this for:

- Dashboards (GlucoLoop, HealthHelper)
- HeartWire UI
- Admin/control panels

#### Mobile App — `apps/mobile-app`

- Flutter
- Dart
- Material / Cupertino widgets

Use this for:

- Companion apps to GlucoLoop / HealthHelper
- Mobile interfaces for your engineering tools

#### Backend — `apps/backend`

- Firebase or Supabase (BaaS)
- SQL (Supabase/PostgreSQL) or Firestore (Firebase)
- Firebase Auth / Supabase Auth
- Acts as the **bridge** between engineering outputs and user-facing apps

---

### 🩺 Domain Systems

Located in [`./systems`](./systems).

These are **product-level architectures** built on top of the Engineering and App stacks.  
Each system has its own README with data models, API design, and roadmap (MVP → v1.0 → v2.0).

#### 📈 GlucoLoop — Closed-Loop Glucose Insights

Folder: [`systems/glucoloop`](./systems/glucoloop)

- Ingests CGM/sensor data.
- Cleans and processes streams with Python.
- Uses MATLAB/Python models for trend prediction & risk scoring.
- Exposes insights via backend APIs.
- Surfaces alerts and summaries in web/mobile apps.

See: [`systems/glucoloop/README.md`](./systems/glucoloop/README.md)

---

#### 💻 HeartWire — Personal + Startup Hub

Folder: [`systems/heartwire`](./systems/heartwire)

- Central hub for portfolio, apps, dashboards, and experiments.
- Connects engineering tools and the app stack into one interface.
- Acts as the “front door” to your ecosystem (public + private views).

See: [`systems/heartwire/README.md`](./systems/heartwire/README.md)

---

#### 🩹 HealthHelper — Unified Health Tracking & Analytics

Folder: [`systems/healthhelper`](./systems/healthhelper)

- Aggregates sleep, stress, nutrition, symptoms, and training data.
- Normalizes inputs into a unified health data model.
- Builds correlations, trends, and basic predictions.
- Feeds visualizations and recommendations into dashboards/apps.

See: [`systems/healthhelper/README.md`](./systems/healthhelper/README.md)

---

#### 🤖 JonnyJr — AI Super-Agent & Orchestrator

Folder: [`systems/jonnyjr`](./systems/jonnyjr)

- Orchestrates LLMs, tools, and workflows (GitHub, Notion, APIs, etc.).
- Routes user requests to appropriate agents (homework, projects, research, planning).
- Maintains memory and schedules (reminders, recurring tasks).
- Acts as the “AI brain” behind the ecosystem.

See: [`systems/jonnyjr/README.md`](./systems/jonnyjr/README.md)

---

## 🗂 Project Structure

Target structure for this repo:

```text
/
├── engineering/                      # All engineering tech stack content
│   ├── 01_comprehensive/
│   ├── 02_optimized/
│   └── shared/
│       ├── datasets/
│       ├── notebooks/
│       └── utils/
│
├── apps/                             # App development framework
│   ├── web-frontend/
│   ├── mobile-app/
│   └── backend/
│
├── systems/                          # Domain-level systems
│   ├── glucoloop/
│   ├── heartwire/
│   ├── healthhelper/
│   └── jonnyjr/
│
├── devops/                           # Infra, Docker, CI/CD templates
│   ├── docker/
│   ├── ci_cd/
│   └── infra/
│       ├── aws/
│       └── gcp/
│
├── docs/                             # Documentation & diagrams
│   ├── README-ENGINEERING.md
│   ├── README-APPS.md
│   ├── README-SYSTEMS.md
│   └── diagrams/
│       └── unified_architecture.png
│
└── .github/
    └── workflows/                    # CI/CD (GitHub Actions)
