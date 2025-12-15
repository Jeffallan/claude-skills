# Agent to Skill Conversion Analysis

## Summary

| Metric | Count |
|--------|-------|
| **Total Agents** | 117 |
| **Recommend CONVERT** | 35 |
| **Recommend ENHANCE** | 18 |
| **Recommend IGNORE** | 64 |

## Scoring System

Each agent scored on 5 dimensions (0-5 each, max 25 points):

| Dimension | 0 | 5 |
|-----------|---|---|
| **Scope Alignment** | Not dev-focused | Core dev workflow |
| **Uniqueness** | Duplicate of existing skill | Completely new capability |
| **Dev Value** | Rarely used | Daily use |
| **Content Depth** | Thin/generic | Rich domain expertise |
| **Complexity** | Very hard to convert | Straightforward |

**Decision Thresholds:**
- 20-25: CONVERT (Priority 1)
- 15-19: CONVERT (Priority 2)
- 10-14: ENHANCE existing skill
- 0-9: IGNORE

---

## Decision Matrix

### CONVERT - New Skills (35 agents)

| Agent | Category | Score | Priority | Notes |
|-------|----------|-------|----------|-------|
| python-pro | Language | 24 | P1 | High-value, rich ecosystem (Django/FastAPI refs exist but general Python missing) |
| typescript-pro | Language | 24 | P1 | High-value, complements existing JS-focused skills |
| javascript-pro | Language | 23 | P1 | Core web dev, distinct from framework skills |
| golang-pro | Language | 22 | P1 | Growing adoption, cloud-native focus |
| rust-engineer | Language | 21 | P1 | Systems programming, unique domain |
| sql-pro | Language | 22 | P1 | Universal DB skill, high daily use |
| nextjs-developer | Framework | 23 | P1 | React ecosystem extension, very popular |
| vue-expert | Framework | 21 | P1 | Major framework, no current coverage |
| angular-architect | Framework | 20 | P1 | Enterprise frontend, distinct patterns |
| spring-boot-engineer | Framework | 21 | P1 | Java enterprise, large user base |
| laravel-specialist | Framework | 20 | P1 | PHP ecosystem leader |
| rails-expert | Framework | 19 | P2 | Ruby ecosystem, convention-focused |
| graphql-architect | API | 22 | P1 | Distinct from REST, growing adoption |
| kubernetes-specialist | Infra | 23 | P1 | Critical cloud-native skill |
| terraform-engineer | Infra | 21 | P1 | IaC standard, complements DevOps |
| postgres-pro | Database | 21 | P1 | Most popular DB, deep optimization content |
| cli-developer | Tooling | 20 | P1 | Dev tooling focus, unique niche |
| api-designer | API | 19 | P2 | Complements implementation skills |
| websocket-engineer | Specialization | 18 | P2 | Real-time systems, distinct domain |
| microservices-architect | Architecture | 19 | P2 | Extends architecture-designer |
| cpp-pro | Language | 18 | P2 | Systems/game dev, niche but deep |
| php-pro | Language | 17 | P2 | Large legacy + modern ecosystem |
| swift-expert | Language | 17 | P2 | iOS/macOS development |
| kotlin-specialist | Language | 17 | P2 | Android + server-side |
| csharp-developer | Language | 18 | P2 | .NET ecosystem |
| java-architect | Language | 18 | P2 | Enterprise Java |
| dotnet-core-expert | Framework | 17 | P2 | Modern .NET |
| database-optimizer | Database | 18 | P2 | Performance focus, complements postgres-pro |
| cloud-architect | Infra | 18 | P2 | Multi-cloud strategy |
| mcp-developer | Tooling | 19 | P2 | Claude ecosystem specific, unique value |
| sre-engineer | Operations | 17 | P2 | Reliability engineering patterns |
| chaos-engineer | Testing | 16 | P2 | Resilience testing, unique approach |
| legacy-modernizer | Specialization | 16 | P2 | Migration patterns, practical value |
| embedded-systems | Specialization | 15 | P2 | IoT/hardware, niche but distinct |
| game-developer | Specialization | 15 | P2 | Game dev patterns, unique domain |

### ENHANCE - Extend Existing Skills (18 agents)

| Agent | Target Skill | Score | Enhancement Notes |
|-------|--------------|-------|-------------------|
| backend-developer | fullstack-guardian | 14 | Add backend-specific patterns |
| frontend-developer | react-expert | 13 | Generalize beyond React |
| fullstack-developer | fullstack-guardian | 12 | Already covered, minor additions |
| mobile-developer | react-native-expert | 13 | Cross-platform patterns |
| mobile-app-developer | flutter-expert | 12 | Native dev patterns |
| qa-expert | test-master | 14 | Expand QA methodology |
| test-automator | test-master | 13 | Add automation frameworks |
| performance-engineer | monitoring-expert | 14 | Add perf testing depth |
| platform-engineer | devops-engineer | 13 | Platform engineering patterns |
| deployment-engineer | devops-engineer | 12 | Deployment strategies |
| security-engineer | secure-code-guardian | 14 | Infrastructure security |
| penetration-tester | security-reviewer | 13 | Offensive techniques |
| incident-responder | devops-engineer | 11 | Incident handling |
| devops-incident-responder | devops-engineer | 11 | Production incident response |
| database-administrator | postgres-pro (new) | 12 | DBA operations |
| documentation-engineer | code-documenter | 14 | Doc systems engineering |
| api-documenter | code-documenter | 13 | API doc specialization |
| technical-writer | code-documenter | 11 | General tech writing |

### IGNORE - Out of Scope or Duplicate (64 agents)

#### Multi-Agent Coordination (12) - Meta-level, not dev skills
| Agent | Score | Reason |
|-------|-------|--------|
| multi-agent-coordinator | 6 | Meta orchestration, not dev-focused |
| agent-organizer | 5 | Agent management, not code |
| task-distributor | 5 | Task allocation, not dev skill |
| workflow-orchestrator | 7 | Process design, too abstract |
| context-manager | 5 | State management meta-level |
| error-coordinator | 6 | Error handling meta-level |
| knowledge-synthesizer | 5 | Knowledge extraction, not dev |
| performance-monitor | 7 | Overlaps monitoring-expert |

#### Business/Strategy (9) - Not technical implementation
| Agent | Score | Reason |
|-------|-------|--------|
| product-manager | 8 | Product strategy, not code |
| project-manager | 7 | Project management, not dev |
| business-analyst | 6 | Requirements, overlaps feature-forge |
| scrum-master | 5 | Process facilitation |
| sales-engineer | 4 | Pre-sales, not implementation |
| customer-success-manager | 3 | Customer relations |
| legal-advisor | 4 | Legal/compliance advice |
| risk-manager | 6 | Risk assessment, not dev |
| quant-analyst | 7 | Financial modeling, niche |

#### Research/Analytics (8) - Not code implementation
| Agent | Score | Reason |
|-------|-------|--------|
| research-analyst | 5 | General research |
| data-researcher | 6 | Data discovery, not engineering |
| market-researcher | 4 | Market analysis |
| competitive-analyst | 4 | Competitive intelligence |
| trend-analyst | 4 | Trend forecasting |
| search-specialist | 6 | Information retrieval |
| ux-researcher | 7 | User research, not code |
| data-analyst | 8 | Analysis, not engineering |

#### Content/Marketing (4) - Not dev-focused
| Agent | Score | Reason |
|-------|-------|--------|
| content-marketer | 3 | Marketing content |
| seo-specialist | 5 | SEO optimization |
| ui-designer | 8 | Visual design, not code |
| wordpress-master | 9 | CMS-specific, narrow scope |

#### Security/Compliance Audit (4) - Review-only, limited scope
| Agent | Score | Reason |
|-------|-------|--------|
| security-auditor | 9 | Overlaps security-reviewer |
| compliance-auditor | 7 | Compliance checking |
| accessibility-tester | 9 | A11y testing, could enhance test-master |
| architect-reviewer | 9 | Overlaps architecture-designer |

#### Duplicates or Narrow Scope (19)
| Agent | Score | Reason |
|-------|-------|--------|
| debugger | 9 | Duplicate of debugging-wizard |
| error-detective | 8 | Overlaps debugging-wizard |
| code-reviewer | 9 | Already exists as skill |
| django-developer | 8 | Duplicate of django-expert |
| react-specialist | 8 | Duplicate of react-expert |
| flutter-expert (agent) | 8 | Already exists as skill |
| devops-engineer (agent) | 8 | Already exists as skill |
| prompt-engineer | 7 | LLM prompting, narrow |
| llm-architect | 8 | LLM systems, narrow |
| machine-learning-engineer | 9 | ML ops, specialized |
| ml-engineer | 8 | Duplicate ML role |
| mlops-engineer | 8 | ML infrastructure |
| data-engineer | 9 | Data pipelines, could be separate skill |
| data-scientist | 8 | Data science, not dev |
| nlp-engineer | 7 | NLP specific, narrow |
| ai-engineer | 8 | AI systems, broad/vague |
| fintech-engineer | 8 | Financial systems, niche |
| payment-integration | 9 | Payment specific, narrow |
| blockchain-developer | 7 | Web3, niche |
| iot-engineer | 7 | IoT specific, narrow |
| network-engineer | 8 | Network infra, not dev |
| dotnet-framework-4.8-expert | 6 | Legacy .NET, narrow |
| electron-pro | 9 | Desktop apps, could convert |
| tooling-engineer | 9 | Overlaps cli-developer |
| build-engineer | 9 | Build systems, could enhance devops |
| refactoring-specialist | 9 | Could enhance code-reviewer |
| dependency-manager | 8 | Package management, narrow |
| git-workflow-manager | 9 | Git patterns, narrow |
| dx-optimizer | 8 | DX tooling, overlaps others |

---

## Conversion Priority Order

### Phase 1 - High Impact (15 skills)
1. python-pro
2. typescript-pro
3. javascript-pro
4. nextjs-developer
5. kubernetes-specialist
6. sql-pro
7. graphql-architect
8. postgres-pro
9. golang-pro
10. vue-expert
11. terraform-engineer
12. rust-engineer
13. angular-architect
14. spring-boot-engineer
15. cli-developer

### Phase 2 - Medium Impact (12 skills)
16. laravel-specialist
17. api-designer
18. mcp-developer
19. websocket-engineer
20. microservices-architect
21. cloud-architect
22. java-architect
23. csharp-developer
24. cpp-pro
25. swift-expert
26. kotlin-specialist
27. database-optimizer

### Phase 3 - Niche/Specialized (8 skills)
28. php-pro
29. rails-expert
30. dotnet-core-expert
31. sre-engineer
32. chaos-engineer
33. legacy-modernizer
34. embedded-systems
35. game-developer

---

## Enhancement Recommendations

### High Priority Enhancements

| Existing Skill | Agents to Merge | New Capabilities |
|----------------|-----------------|------------------|
| **test-master** | qa-expert, test-automator | QA methodology, automation frameworks |
| **code-documenter** | documentation-engineer, api-documenter, technical-writer | Doc systems, API specs |
| **devops-engineer** | platform-engineer, deployment-engineer, incident-responder | Platform eng, deployments, incidents |
| **security-reviewer** | penetration-tester, security-engineer | Pentesting, infra security |
| **monitoring-expert** | performance-engineer | Performance testing |

### Consider for Future

| Existing Skill | Potential Enhancement |
|----------------|----------------------|
| fullstack-guardian | backend-developer, frontend-developer patterns |
| react-expert | frontend-developer generalization |
| architecture-designer | microservices-architect patterns |

---

## Existing Skills Reference (20)

| Skill | Category | Status |
|-------|----------|--------|
| fullstack-guardian | Full-stack | Active |
| code-documenter | Documentation | Active |
| spec-miner | Analysis | Active |
| fastapi-expert | Backend/Python | Active |
| monitoring-expert | Operations | Active |
| devops-engineer | Operations | Active |
| debugging-wizard | Debug | Active |
| test-master | Testing | Active |
| django-expert | Backend/Python | Active |
| code-reviewer | Review | Active |
| nestjs-expert | Backend/Node | Active |
| playwright-expert | Testing | Active |
| react-expert | Frontend | Active |
| architecture-designer | Architecture | Active |
| secure-code-guardian | Security | Active |
| feature-forge | Requirements | Active |
| react-native-expert | Mobile | Active |
| flutter-expert | Mobile | Active |
| security-reviewer | Security | Active |

---

## Next Steps

1. **Start with Phase 1 conversions** - highest dev value, most frequently used
2. **Apply enhancements** to existing skills during conversion process
3. **Re-evaluate IGNORE list** after Phase 1 completion - some may become higher priority
4. **Consider data-engineer** as potential future skill (scored 9, borderline)
