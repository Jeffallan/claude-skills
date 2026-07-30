---
name: lms-platform-architect
description: Designs and architects Learning Management System (LMS) platforms using NestJS (backend) and Next.js (frontend). Covers module decomposition, database schema design, RBAC for multi-role platforms (admin/instructor/student), course/enrollment/assessment domain modeling, content delivery and video/file storage strategy, notification and payment integration, multi-tenancy, caching, and scalability planning. Use when the user is designing, planning, or reviewing the architecture of an LMS, e-learning platform, course marketplace, or corporate training system, or explicitly asks for system design, module breakdown, or a build plan for such a platform.
license: MIT
metadata:
  author: https://github.com/shahria-dev
  version: "1.0.0"
  domain: architecture
  triggers: LMS, learning management system, e-learning platform, course platform, NestJS, Next.js, system design, module architecture, education platform
  role: specialist
  scope: system-design
  output-format: architecture
  related-skills: nestjs-expert, nextjs-developer, architecture-designer, database-optimizer, api-designer, secure-code-guardian
---

# LMS Platform Architect

Guidance for architecting Learning Management System (LMS) platforms with a **NestJS backend** and **Next.js frontend**. Use this skill for system design, module decomposition, database schema planning, and build-plan structuring — not for writing feature-level implementation code (defer to **NestJS Expert** / **Next.js Developer** for that).

## When to Reach for This Skill

- Starting a new LMS / e-learning / course-marketplace / corporate-training platform from scratch
- Reviewing or refactoring an existing platform's module boundaries
- Planning a sprint/build-plan breakdown across a small team
- Deciding how to model courses, enrollments, assessments, and roles
- Choosing content-delivery, storage, and video-streaming strategy
- Designing multi-tenancy or white-label support for an LMS

## Core Domain Model

Every LMS, regardless of size, revolves around five core entities. Model these first before adding secondary features:

1. **User** — role-based (Admin, Instructor, Student, and optionally Org Admin for B2B). Prefer a single `User` table with a `role` enum plus role-specific profile tables, over separate tables per role — this keeps auth simple.
2. **Course** — owned by an Instructor, contains **Modules** → **Lessons** (video/text/quiz/assignment). Model course structure as a tree (course → module → lesson), not flat.
3. **Enrollment** — join entity between User and Course, carries `progress`, `status` (active/completed/expired), and `enrolledAt`. This is where most business logic lives (progress tracking, certificates, access expiry).
4. **Assessment** — Quiz/Assignment with `Question`, `Submission`, `Grade`. Keep grading logic separate from content delivery.
5. **Content Asset** — video/PDF/SCORM package, referenced by Lesson, stored externally (S3/Cloud storage), never in the DB.

Secondary modules (add only as needed): Payments/Subscriptions, Notifications, Certificates, Discussion/Forum, Live Sessions, Analytics/Reporting, Reviews & Ratings.

## Recommended Module Breakdown (NestJS)

Structure the NestJS backend as one module per bounded context — this maps directly to a sprint/feature-tracking plan:


src/
├── auth/ # JWT, refresh tokens, role guards
├── users/ # profile, role management
├── courses/ # CRUD, module/lesson tree
├── enrollments/ # enroll, progress tracking, access control
├── assessments/ # quizzes, assignments, grading
├── content/ # signed upload/download URLs, transcoding hooks
├── payments/ # Stripe/SSLCommerz/bKash integration, invoices
├── notifications/ # email/push/in-app, queued via BullMQ
├── certificates/ # PDF generation on course completion
├── analytics/ # instructor dashboards, admin reporting
└── common/ # guards, interceptors, DTOs, pipes
Guiding rules:
- Each module owns its own entities/repositories — avoid cross-module direct DB access; communicate via services or domain events.
- Use NestJS's `EventEmitterModule` or a message queue (BullMQ/RabbitMQ) for cross-module side effects (e.g., `enrollment.completed` → trigger `certificates` + `notifications`), rather than tight coupling.
- Put authorization logic in guards (`RolesGuard`, `EnrollmentAccessGuard`), not scattered in controllers.

## Recommended Structure (Next.js)
app/
├── (marketing)/ # public course catalog, landing pages — SSG/ISR
├── (auth)/ # login, register, password reset
├── (student)/dashboard/ # enrolled courses, progress — Server Components + client player
├── (instructor)/studio/ # course authoring, analytics
├── (admin)/console/ # user mgmt, platform config
└── api/ # route handlers only for BFF concerns (webhooks, signed URL proxying)
- Use **Server Components** for catalog/browse pages (SEO matters for course discovery) and **Client Components** only for interactive pieces (video player, quiz, progress bar).
- Fetch data via a typed API client generated from the NestJS OpenAPI spec — keeps frontend/backend contracts in sync as the platform grows.
- Gate role-specific routes (`(instructor)`, `(admin)`) with middleware checking the JWT/session, not just client-side checks.

## System Design Decisions

### Content Delivery & Storage
- Store video/files in object storage (S3-compatible), never on the app server. Generate **signed URLs** (short-lived) via the `content` module rather than proxying large files through NestJS.
- For video: use a dedicated streaming/transcoding pipeline (e.g., Mux, Cloudflare Stream, or self-hosted HLS via FFmpeg + S3) instead of serving raw MP4 — enables adaptive bitrate and prevents downloads.
- Cache signed-URL generation and course metadata with Redis; do not cache user-specific progress data aggressively.

### Access Control & Progress
- Enrollment status gates content access — check it at the API layer (guard), not just hide UI elements.
- Track progress at the lesson level (`completed`, `lastPosition` for video) and roll it up to course-level percentage; avoid recalculating on every request — update incrementally on lesson-complete events.

### Multi-Tenancy (if B2B/white-label is in scope)
- Decide early: **shared schema with `organizationId` on every table** (simpler, cheaper, fine up to moderate scale) vs. **schema-per-tenant** (stronger isolation, more ops overhead). Default to shared schema with `organizationId` unless the client explicitly requires data isolation guarantees.

### Payments
- Separate "purchase" (one-time or subscription) from "enrollment" — a purchase grants entitlement, enrollment tracks consumption. This separation makes refunds, gifting, and bundle/coupon logic much easier to reason about later.

### Scalability Ordering
When a client asks "will this scale," address in this order: (1) DB indexing on `enrollments(userId, courseId)` and `progress` lookups, (2) Redis caching for catalog/course-metadata reads, (3) offloading video entirely to a CDN/streaming service, (4) horizontal scaling of the NestJS API behind a load balancer (stateless, so straightforward), (5) read replicas only once read load is measurably the bottleneck. Don't reach for read replicas or microservices split before the first three are in place.

## Decision Tree: Module Granularity

- **Small team (1-3 devs), MVP** → Modular monolith (single NestJS app, module folders as above). Do not split into microservices yet.
- **Growing platform, distinct scaling needs** (e.g., video transcoding is CPU-heavy) → Extract only that concern into a worker service, keep the rest monolithic.
- **True multi-team, multi-product org** → Consider splitting `payments` and `notifications` into separate services behind a message queue, since they're the most reusable across products.

## Suggested Build-Plan Structure

When asked to produce a feature/module tracking plan (e.g., for a spreadsheet or sprint board), organize by the module list above, and within each module track: feature name, priority (P0/P1/P2), owner, status, and dependency on other modules (e.g., `certificates` depends on `enrollments` + `assessments`). Sequence modules so `auth` → `users` → `courses` → `enrollments` ship before `payments`, `analytics`, and `certificates`, since the latter all depend on the former.

## Anti-Patterns to Flag

- Storing video/large files directly in Postgres/Mongo — always object storage + signed URLs.
- Putting business rules (progress calculation, access gating) in the frontend only.
- One giant `CourseModule` that also owns payments, notifications, and grading — split by bounded context.
- Recomputing full-course progress on every page load instead of incrementally updating on lesson completion.
- Hard-deleting enrollments/submissions — soft-delete or archive, since grading disputes and refunds need historical data.

[Documentation](https://jeffallan.github.io/claude-skills/skills/architecture/lms-platform-architect/)
