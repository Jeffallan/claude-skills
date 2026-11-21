# Red Team Adversarial

Adversarial thinking and red teaming for finding weaknesses before adversaries do.

## Core Principle

Red teaming asks: **"If someone wanted to break, exploit, or game this, how would they do it?"** The Fool adopts the mindset of an adversary — not to cause harm, but to find vulnerabilities before real adversaries do. This applies beyond security: competitors, disgruntled users, perverse incentives, and regulatory challenges are all adversarial forces.

## Process

1. **Identify the asset** — What are you protecting? (system, decision, strategy, product)
2. **Construct adversary personas** — Who would attack this and why?
3. **Map attack vectors** — How would each persona exploit weaknesses?
4. **Assess impact** — Rank by likelihood x impact
5. **Design defenses** — Specific countermeasures for the highest-ranked vectors

## Adversary Persona Construction

Generic "attackers" produce generic findings. Specific personas produce actionable insights.

### Persona Template

| Field | Description |
|-------|-------------|
| **Role** | Who is this adversary? |
| **Motivation** | Why would they attack? |
| **Capability** | What resources and skills do they have? |
| **Access** | What do they already have access to? |
| **Constraints** | What limits them? |

### Common Adversary Personas

| Persona | Motivation | Typical Vectors |
|---------|-----------|----------------|
| **External Attacker** | Financial gain, data theft | API exploitation, credential stuffing, injection attacks |
| **Competitor** | Market advantage | Feature copying, talent poaching, FUD campaigns |
| **Disgruntled Insider** | Revenge, financial gain | Privilege escalation, data exfiltration, sabotage |
| **Careless User** | None (accidental) | Misconfiguration, weak passwords, sharing credentials |
| **Regulator** | Compliance enforcement | Audit findings, data handling violations, accessibility gaps |
| **Opportunistic Gamer** | Personal benefit | Exploiting loopholes in business logic, referral fraud |
| **Activist** | Ideological goals | Public embarrassment, data leaks, service disruption |

### Domain-Specific Personas

| Domain | Key Adversary | Focus |
|--------|--------------|-------|
| E-commerce | Fraudster | Payment bypass, coupon abuse, fake returns |
| SaaS | Free-tier abuser | Rate limit evasion, multi-accounting, resource hoarding |
| Marketplace | Bad-faith seller | Fake listings, review manipulation, escrow games |
| API Platform | Scraper | Rate limit bypass, data harvesting, reverse engineering |
| Social Platform | Troll/bot farm | Spam, manipulation, fake engagement |

## Attack Vector Identification

### By Category

| Category | Vectors | Example |
|----------|---------|---------|
| **Technical** | Injection, auth bypass, race conditions, SSRF | SQL injection in search parameter |
| **Business Logic** | Workflow bypass, state manipulation, price tampering | Applying expired coupon via API replay |
| **Social** | Phishing, pretexting, authority exploitation | "I'm the CEO, I need access now" |
| **Operational** | Supply chain, dependency poisoning, insider threat | Compromised npm package in build pipeline |
| **Information** | Data leakage, metadata exposure, timing attacks | User enumeration via login error messages |
| **Economic** | Resource exhaustion, denial of wallet, asymmetric cost | Lambda invocation flood causing $50K bill |

### Attack Tree Construction

For complex systems, build attack trees to map paths to a goal.

```
Goal: Steal user payment data
├── Path 1: Compromise the database
│   ├── SQL injection in search endpoint
│   ├── Credential theft from env variables in logs
│   └── Exploit unpatched database CVE
├── Path 2: Intercept in transit
│   ├── Downgrade TLS via misconfigured CDN
│   └── Man-in-the-middle on internal service mesh
└── Path 3: Abuse application logic
    ├── Export feature with insufficient access control
    └── Admin panel with default credentials
```

## Perverse Incentive Detection

Systems create incentives. Sometimes those incentives reward the wrong behavior.

### Questions to Surface Perverse Incentives

| Question | What It Reveals |
|----------|----------------|
| "How will people game this?" | Loopholes in business logic |
| "What behavior does this reward that we don't want?" | Misaligned incentives |
| "What's the cheapest way to get the reward without the effort?" | Shortcut exploitation |
| "If we measure X, what Y gets sacrificed?" | Goodhart's Law in action |
| "Who benefits from this failing?" | Adversaries with motive |

### Common Perverse Incentive Patterns

| Pattern | Example | Consequence |
|---------|---------|-------------|
| Metric gaming | "Lines of code" as productivity metric | Verbose, unmaintainable code |
| Reward hacking | Referral bonus with no verification | Fake accounts for self-referral |
| Race to the bottom | "Fastest response time" as SLA | Teams avoid taking complex tickets |
| Cobra effect | Bounty for reporting bugs | Team introduces bugs to claim bounties |
| Information asymmetry | Users know more than the system | Adverse selection in marketplace pricing |

## Competitive Response Analysis

When the "adversary" is a competitor.

| Scenario | Analysis Framework |
|----------|-------------------|
| Feature parity | What can they copy? How fast? What's our defensible moat? |
| Price war | Can they sustain lower prices? What's their cost structure? |
| Talent poaching | Which roles are critical? How replaceable? What's our retention advantage? |
| Platform risk | Are we dependent on their platform? What's the switch cost? |
| FUD campaign | What claims could they make? Which are hardest to refute? |

## Output Template

```markdown
## Red Team Analysis: [Target]

### Asset Under Assessment

[What we're protecting and why it matters]

### Adversary Profiles

#### Adversary 1: [Name/Role]
- **Motivation:** [Why they attack]
- **Capability:** [What they can do]
- **Access:** [What they start with]

#### Adversary 2: [Name/Role]
- **Motivation:** [Why they attack]
- **Capability:** [What they can do]
- **Access:** [What they start with]

### Attack Vectors (Ranked)

| # | Vector | Adversary | Likelihood | Impact | Risk Score |
|---|--------|-----------|-----------|--------|------------|
| 1 | [Specific attack] | [Who] | High/Med/Low | High/Med/Low | [L x I] |
| 2 | [Specific attack] | [Who] | High/Med/Low | High/Med/Low | [L x I] |
| 3 | [Specific attack] | [Who] | High/Med/Low | High/Med/Low | [L x I] |

### Perverse Incentives

| Incentive Created | Unintended Behavior | Severity |
|-------------------|-------------------|----------|
| [What the system rewards] | [How it gets gamed] | High/Med/Low |

### Recommended Defenses

| Attack Vector | Defense | Effort | Priority |
|--------------|---------|--------|----------|
| #1 | [Specific countermeasure] | Low/Med/High | Immediate/Next sprint/Backlog |
| #2 | [Specific countermeasure] | Low/Med/High | Immediate/Next sprint/Backlog |
| #3 | [Specific countermeasure] | Low/Med/High | Immediate/Next sprint/Backlog |
```
