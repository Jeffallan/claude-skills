# Interview Questions

> Reference for: Feature Forge
> Load when: Gathering requirements

## PM Hat Questions

Focus on user value and business goals.

| Area | Questions |
|------|-----------|
| **Problem** | What problem does this solve? Who experiences this problem? How often? |
| **Users** | Who are the target users? What are their goals? Technical level? |
| **Value** | How will users benefit? What's the business value? ROI? |
| **Scope** | What's in scope? What's explicitly out of scope? MVP vs full version? |
| **Success** | How will we measure success? Key metrics? |
| **Priority** | Is this a must-have, should-have, or nice-to-have? |

### Example PM Questions

```markdown
For a "User Export" feature:
- Who needs to export data and why?
- What format do they need (CSV, JSON, Excel)?
- How much data? 100 rows or 1 million?
- Is this for compliance (GDPR) or convenience?
- How often will this be used?
- What's the deadline?
```

## Dev Hat Questions

Focus on technical feasibility and edge cases.

| Area | Questions |
|------|-----------|
| **Integration** | What systems does this touch? APIs, databases, services? |
| **Security** | Authentication required? Data sensitivity (PII, PCI)? |
| **Performance** | Expected load? Response time requirements? Async OK? |
| **Edge Cases** | What happens when X fails? Empty states? Limits? |
| **Data** | What's stored? Retention period? Backup needs? |
| **Dependencies** | External services? Rate limits? Costs? |

### Example Dev Questions

```markdown
For a "User Export" feature:
- What fields to include? Are any sensitive (passwords, tokens)?
- Max export size? Need streaming or background job?
- Should include soft-deleted records?
- What happens if export fails midway?
- File retention - how long to keep generated files?
- Need progress indicator for large exports?
```

## Interview Flow

### Phase 1: Discovery (5-10 min)
```markdown
1. "Tell me about this feature in your own words"
2. "What problem are we solving?"
3. "Who will use this and how often?"
4. "What does success look like?"
```

### Phase 2: Details (10-15 min)
```markdown
1. "Walk me through the user journey"
2. "What are the must-haves vs nice-to-haves?"
3. "Any constraints - time, budget, technical?"
4. "Are there existing similar features we should match?"
```

### Phase 3: Edge Cases (5-10 min)
```markdown
1. "What happens when [X fails]?"
2. "What if there's no data?"
3. "What about very large datasets?"
4. "Any special permissions needed?"
```

### Phase 4: Validation (5 min)
```markdown
1. "Let me summarize what I heard..."
2. "Anything I missed?"
3. "Any questions for me?"
```

## Quick Reference

| Phase | Focus | Time |
|-------|-------|------|
| Discovery | Problem, users, value | 5-10 min |
| Details | Journey, scope, constraints | 10-15 min |
| Edge Cases | Failures, limits, security | 5-10 min |
| Validation | Summary, gaps | 5 min |
