# Skills Quick Reference Guide

## When to Use Each Skill

### Planning & Requirements
- **Feature Forge**: Creating new features, gathering requirements, writing specs
- **Spec Miner**: Analyzing existing code, reverse-engineering specifications
- **Architecture Designer**: System design, choosing architectures, ADRs

### Implementation
- **Fullstack Guardian**: Implementing features across full stack
- **NestJS Expert**: Building TypeScript backend APIs with NestJS
- **Django Expert**: Building Python web apps with Django/DRF
- **FastAPI Expert**: Building async Python APIs with FastAPI
- **React Expert**: Building React web applications
- **React Native Expert**: Building cross-platform mobile apps (React Native)
- **Flutter Expert**: Building cross-platform apps with Flutter

### Quality & Testing
- **Test Master**: Overall testing strategy (unit, integration, E2E, performance, security)
- **Playwright Expert**: Browser automation and E2E testing
- **Code Reviewer**: Conducting thorough code reviews
- **Code Documenter**: Adding inline documentation and API docs

### Operations
- **DevOps Engineer**: CI/CD, deployment, infrastructure
- **Monitoring Expert**: Logging, metrics, tracing, alerting

### Debugging & Troubleshooting
- **Debugging Wizard**: Systematic debugging across all languages

### Security
- **Secure Code Guardian**: Writing secure code, preventing vulnerabilities
- **Security Reviewer**: Security code review and SAST analysis

## Skill Workflows

### New Feature Development
1. **Feature Forge** - Define requirements and spec
2. **Architecture Designer** - Design system architecture (if complex)
3. **Fullstack Guardian** + Framework Skills - Implement
4. **Test Master** + **Playwright Expert** - Test comprehensively
5. **Code Reviewer** - Review code
6. **Security Reviewer** - Security review
7. **DevOps Engineer** - Deploy
8. **Monitoring Expert** - Add observability

### Bug Fixing
1. **Debugging Wizard** - Identify root cause
2. **Fullstack Guardian** + Framework Skills - Fix
3. **Test Master** - Add regression tests
4. **Code Reviewer** - Review fix
5. **DevOps Engineer** - Deploy

### Code Review Process
1. **Code Reviewer** - General code review
2. **Security Reviewer** - Security-focused review
3. **Architecture Designer** - Architectural review (if needed)

### Legacy Code Analysis
1. **Spec Miner** - Reverse-engineer specs
2. **Architecture Designer** - Document architecture
3. **Code Documenter** - Add missing documentation
4. **Security Reviewer** - Security audit

## Framework Decision Tree

### Backend API
- **TypeScript** → NestJS Expert
- **Python + Django** → Django Expert  
- **Python + Async** → FastAPI Expert

### Frontend
- **Web Application** → React Expert
- **Mobile (JavaScript)** → React Native Expert
- **Mobile (Dart)** → Flutter Expert

### Testing
- **E2E Browser Tests** → Playwright Expert
- **All Other Testing** → Test Master

## Skill Combinations

Common combinations for maximum effectiveness:

### Full Feature Development
- Feature Forge + Fullstack Guardian + Framework Skills + Test Master + DevOps Engineer

### Security-Focused Development
- Secure Code Guardian + Fullstack Guardian + Security Reviewer + Test Master

### Performance Optimization
- Architecture Designer + Monitoring Expert + Framework Skills + Test Master

### Documentation Sprint
- Code Documenter + Spec Miner + Architecture Designer

### DevOps Setup
- DevOps Engineer + Monitoring Expert + Architecture Designer

## Tips for Effective Use

1. **Be Specific**: Mention the technology/framework to activate the right skill
2. **Context Matters**: Provide context about your tech stack
3. **Combine Skills**: Don't hesitate to ask for multiple perspectives
4. **Security First**: Always run Security Reviewer on critical code
5. **Document**: Use Code Documenter for public APIs and complex logic

## Examples

### Good Prompts
- "Help me design a microservices architecture for an e-commerce platform" → Architecture Designer
- "Implement user authentication in my NestJS API" → NestJS Expert + Secure Code Guardian
- "Debug this memory leak in my React app" → Debugging Wizard + React Expert
- "Review this code for security issues" → Security Reviewer
- "Set up monitoring for my FastAPI application" → Monitoring Expert + FastAPI Expert

### Specific Requests
- "Generate OpenAPI docs for my Django REST API" → Code Documenter
- "Write Playwright tests for the login flow" → Playwright Expert
- "Analyze this legacy codebase and create a spec" → Spec Miner
- "Help me implement RBAC in NestJS" → NestJS Expert + Secure Code Guardian
