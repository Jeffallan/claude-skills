# Superpowers: A Research Document on obra/superpowers

## Attribution

**Repository:** https://github.com/obra/superpowers
**Author:** Jesse Vincent (@obra)
**License:** MIT
**Stars:** 10.1k
**Last Updated:** December 2025

---

## 1. Executive Summary

Superpowers is a complete software development workflow system for AI coding agents (particularly Claude Code) that transforms how agents approach software development. Rather than allowing agents to jump directly into code generation, Superpowers enforces a disciplined, systematic approach through composable "skills" that guide agents through proper software engineering practices.

The framework emphasizes methodical development: interactive design refinement, incremental validation with users, detailed implementation planning, test-driven development, and subagent-driven execution with multi-stage reviews. This structured approach enables Claude to work autonomously for extended periods (2+ hours) without deviating from plans or sacrificing code quality.

**Key Value Propositions:**
- Enforces true test-driven development through iron laws
- Prevents common AI coding pitfalls through systematic verification
- Reduces technical debt through YAGNI and DRY principles
- Enables autonomous agent work through structured workflows
- Provides reusable patterns for complex development tasks

**Core Technologies:** Shell (62.2%), JavaScript (26.7%), Python (6.1%), TypeScript (4.6%)

---

## 2. Repository Overview

### Purpose
Superpowers is a skills framework for Claude Code that provides structured workflows for software development. It replaces ad-hoc code generation with systematic processes that emphasize planning, testing, verification, and iterative refinement.

### Repository Statistics
- **Stars:** 10.1k
- **Forks:** 854
- **License:** MIT License
- **Latest Version:** 3.6.2 (as of December 2025)

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `skills/` | Core skills library with 14+ development workflow skills |
| `agents/` | Agent configurations for different development roles |
| `commands/` | CLI command implementations for workflow automation |
| `hooks/` | Integration points for extending functionality |
| `lib/` | Utility libraries supporting the framework |
| `docs/` | Platform-specific documentation and guides |
| `tests/` | Test suites ensuring framework quality |

### Core Workflow Steps

1. **Brainstorming** - Interactive design refinement with users
2. **Git Worktree Setup** - Isolated workspace creation for features
3. **Plan Writing** - Breaking work into bite-sized, testable tasks
4. **Subagent-Driven Execution** - Delegating implementation to fresh agents
5. **Test-Driven Development** - Enforcing red-green-refactor cycles
6. **Code Review Integration** - Two-stage review (spec compliance → quality)
7. **Verification Before Completion** - Evidence-based success claims
8. **Branch Completion and Cleanup** - Proper finishing procedures

### Philosophy

The framework rejects shortcuts and ad-hoc approaches in favor of:
- **Evidence over assumptions** - Verify before claiming completion
- **Tests before code** - No production code without failing tests first
- **Systematic over reactive** - Root cause investigation before fixes
- **Minimal over maximal** - YAGNI ruthlessly applied
- **Process over instinct** - Follow skills exactly as documented

---

## 3. Core Concepts

### The 1% Rule

The foundational principle from `using-superpowers/SKILL.md`:

> **"If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST read the skill. This is not negotiable. This is not optional. You cannot rationalize your way out of this."**

This iron law prevents agents from taking shortcuts or relying on memory/assumptions.

**The Workflow:**
1. Check for applicable skills **BEFORE any response** (even clarifying questions)
2. Invoke the Skill tool if there's minimal relevance
3. Announce the skill's purpose to the user
4. Follow the skill exactly as documented

**Red Flag Rationalizations to Reject:**
- "This is just a simple question, I don't need to check skills"
- "I need to gather information first before consulting skills"
- "I remember what this skill says, no need to re-read it"
- "This skill seems like overkill for this task"

All such thoughts constitute dangerous patterns that undermine systematic discipline.

**Skill Priority:** When multiple skills apply, process skills (brainstorming, debugging) take precedence over implementation skills, as they determine the approach itself.

**Skill Types:**
- **Rigid skills** - Demand exact adherence (e.g., TDD, Verification)
- **Flexible skills** - Allow principle-based adaptation within guardrails

### Testing Iron Laws

From `test-driven-development/SKILL.md`, three non-negotiable rules:

#### Iron Law 1: The Fundamental Rule
**"NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"**

Write code before the test? Delete it and start over. No exceptions.

#### Iron Law 2: Proof Through Observation
**"If you didn't watch the test fail, you don't know if it tests the right thing."**

Mandatory verification: observe the failure before implementation. This proves the test actually validates the intended behavior.

#### Iron Law 3: The Final Rule
**"Production code → test exists and failed first. Otherwise → not TDD"**

No exceptions without explicit human partner approval.

**The Red-Green-Refactor Cycle:**

1. **RED** - Write one minimal failing test demonstrating required behavior
2. **GREEN** - Implement simplest code passing that test only
3. **REFACTOR** - Improve code while keeping tests green

**Key TDD Principles:**

- **Behavior-First Thinking:** Tests-first answer "What should this do?" versus tests-after which ask "What does this do?" Implementation bias corrupts tests written after code completion.
- **Spirit and Letter Alignment:** "Violating the letter of the rules is violating the spirit of the rules." Both strict adherence and genuine principle matter equally.
- **Real Code Over Mocks:** Write tests using real code, not mocks when avoidable
- **One Behavior Per Test:** Clear descriptive naming for each test case
- **Never Rationalize:** Never skip TDD "just this once"
- **Delete Incomplete Work:** Never keep as reference while writing tests

**Common Rejected Rationalizations:**
- "I can manually test this quickly"
- "I'll write tests after to save time"
- "I've already written so much code, I can't delete it now"

### Verification Before Completion

From `verification-before-completion/SKILL.md`, the core principle:

**"NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE"**

Success assertions require concrete verification proof—not assumptions, confidence, or partial checks.

**The Five-Step Verification Process:**

1. **Identify** - Determine which command validates the specific claim
2. **Run** - Execute the full command fresh (not from memory or prior runs)
3. **Read** - Examine complete output and verify exit codes
4. **Verify** - Confirm output supports the claim; if not, state actual status with evidence
5. **Claim** - Only after step 4 succeeds, make the claim backed by evidence

**Omitting any step constitutes verification failure.**

**Apply Verification Before:**
- Any completion or success statements
- Expressing satisfaction about work quality
- Commits, pull requests, or task closures
- Delegating work to other agents

**Red Flags to Avoid:**
- Tentative language: "should," "probably," "seems"
- Claiming success before running fresh commands
- Trusting incomplete checks or agent success reports
- Exclamations of satisfaction: "Done!", "Perfect!", "All set!"

**Common Mistakes:**
- Conflating linter passes with successful builds
- Assuming tests pass without running them
- Accepting agent reports without independent verification
- Running partial verification commands

The non-negotiable standard: **Run commands, examine outputs, then report results.**

---

## 4. Testing Anti-Patterns

From `test-driven-development/testing-anti-patterns.md`, five critical anti-patterns that undermine test quality:

### Anti-Pattern 1: Testing Mock Behavior

**Problem:** Verifying that mocks exist rather than validating actual component functionality.

**Example:**
```javascript
// BAD: Testing the mock, not the component
test('sidebar renders', () => {
  render(<App />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});
```

**Why It Fails:** "You're verifying the mock works, not that the component works." The test passes merely because the mock is present, revealing nothing about real behavior.

**Solution:** Test genuine component output or remove the mock entirely:
```javascript
// GOOD: Testing actual behavior
test('sidebar renders', () => {
  render(<App />);
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});
```

### Anti-Pattern 2: Test-Only Methods in Production

**Problem:** Adding methods to production classes solely for test cleanup purposes.

**Example:**
```javascript
// BAD: Production class polluted with test concerns
class Session {
  constructor() { /* ... */ }

  // Only used in tests!
  destroy() {
    this.cleanup();
  }
}
```

**Why It Fails:** Production code becomes contaminated with test infrastructure, creating confusion about object lifecycle and risking accidental production misuse.

**Solution:** Relocate cleanup logic to test utility functions:
```javascript
// GOOD: Test utilities operate externally
// test/utils.js
export function cleanupSession(session) {
  // Cleanup logic here
}
```

### Anti-Pattern 3: Mocking Without Understanding

**Problem:** Mocking methods without grasping what side effects the real implementation produces.

**Example:**
```javascript
// BAD: Mocking prevents critical side effects
vi.mock('./tools', () => ({
  discoverAndCacheTools: vi.fn()  // Actually writes config file!
}));

// Test fails because config file was never written
```

**Why It Fails:** Over-mocking to "be safe" inadvertently removes critical behavior the test requires, producing misleading pass/fail outcomes.

**Solution:** First run the test with real implementations to observe actual dependencies, then mock only at the appropriate lower level while preserving necessary behavior.

### Anti-Pattern 4: Incomplete Mocks

**Problem:** Creating mock responses containing only fields the immediate test uses, omitting downstream dependencies.

**Example:**
```javascript
// BAD: Partial mock missing fields
const mockResponse = {
  status: 200,
  data: { user: 'test' }
  // Missing metadata.requestId that downstream code needs!
};
```

**Why It Fails:** "Partial mocks hide structural assumptions." Tests pass despite integration failures when real APIs include complete field sets.

**Solution:** Mirror the complete real API response structure:
```javascript
// GOOD: Complete mock matching real API
const mockResponse = {
  status: 200,
  data: { user: 'test' },
  metadata: {
    requestId: 'test-123',
    timestamp: '2025-01-01T00:00:00Z'
  }
};
```

### Anti-Pattern 5: Integration Tests as Afterthought

**Problem:** Treating testing as optional follow-up work rather than integral to implementation.

**Example:**
```
Task: Implement user authentication
Status: ✅ Complete
Tests: TODO
```

**Why It Fails:** "Testing is part of implementation, not optional follow-up." Skipping TDD obscures whether code actually functions as intended.

**Solution:** Follow test-driven development religiously:
1. Write failing tests first
2. Implement to pass
3. Refactor
4. Only then declare completion

---

## 5. Persuasion as Guardrails

The framework employs deliberate persuasion techniques to guide agents toward safe, effective practices. These are not manipulative but rather positive mechanisms channeling discussion toward clarity and feasibility.

### Collaborative Framing

**Technique:** Position designer and user as partners with shared ownership.

**Example Language:** "Help turn ideas into fully formed designs"

**Effect:** Establishes cooperation rather than top-down direction, increasing buy-in and engagement.

### Incremental Validation

**Technique:** Break presentations into small sections (200-300 words) with checkpoints.

**Process:** "Show small sections, checking after each section whether it looks right so far."

**Effect:** Prevents overwhelming users and catches misalignment early before significant work investment.

### Choice Architecture

**Technique:** Prefer multiple choice questions over open-ended prompts.

**Rationale:** Constraining decision space makes responses easier and more predictable.

**Example:**
```
Which approach fits better?
A) REST API with JWT authentication
B) GraphQL with session cookies
C) Something else (please describe)
```

### Sequential Questioning

**Technique:** "Only one question per message"

**Effect:** Prevents cognitive overload and maintains focus. Users can concentrate on single decisions without feeling overwhelmed by simultaneous demands.

### YAGNI Ruthlessly

**Technique:** Explicit principle to "Remove unnecessary features from all designs"

**Effect:** Acts as a persuasive filter, pushing users toward minimalism through framing as disciplined practice rather than constraint.

### Deliberate Pacing with Validation Checkpoints

**Overall Structure:**
1. Understanding (gather requirements)
2. Exploration (discuss options)
3. Design presentation (incremental sections)
4. Validation (checkpoint confirmations)
5. Documentation (formalize decisions)

**Effect:** Creates natural momentum building buy-in through incremental progress visibility.

**Key Insight:** These guardrails function as positive persuasion mechanisms, guiding toward better outcomes without manipulation or coercion.

---

## 6. Subagent-Driven Development

From `subagent-driven-development/SKILL.md`, a sophisticated workflow for delegation and quality assurance.

### Core Principle

**"Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration."**

Dispatch a fresh subagent for each discrete task while implementing a rigorous two-stage review process.

### Two-Stage Review Workflow

The review process follows a strict sequence that must not be reordered:

#### Stage 1: Spec Compliance Review

**Purpose:** Confirm implemented code matches the original specification.

**Reviewer:** Dedicated spec reviewer subagent

**What It Catches:**
- **Over-building** - Unnecessary features not in spec
- **Under-building** - Missing required functionality
- **Requirement gaps** - Misinterpretation of specifications
- **Interpretation issues** - Different understanding of requirements

**Critical Red Flag:** "Start code quality review before spec compliance is ✅ (wrong order)"

**Why Order Matters:** Prevents wasting review effort on code that doesn't meet requirements. Quality review is meaningless if the code doesn't implement the right thing.

#### Stage 2: Code Quality Review

**Timing:** Only after spec compliance approval

**Reviewer:** Dedicated code quality reviewer subagent

**What It Evaluates:**
- Implementation quality
- Maintainability
- Best practices adherence
- Performance considerations
- Code organization

### Review Loop Protocol

**Fix Process:**
1. Reviewer identifies issues
2. **Same implementation subagent** fixes them
3. **Same reviewer** re-examines changes
4. Repeat until approval

**Rationale:** Maintaining the same agent for implementation and fixes prevents context pollution and ensures consistency.

### Key Principles

**Before Implementation:**
- Answer subagent questions completely before work begins
- Provide full task text upfront rather than having subagents read source files
- Ensure specifications are clear and unambiguous

**During Review:**
- Never skip either review stage
- Never accept "close enough" on compliance
- Each reviewer focuses solely on their domain
- Same subagent handles all iterations of a task

**Red Flag Indicators:**
- "The implementer finished suspiciously quickly. Their report may be incomplete, inaccurate, or optimistic."
- Rushing to quality review before spec is confirmed
- Accepting implementation without verification
- Switching subagents mid-task

### Three Verification Categories

**1. Missing Requirements**
- Required functionality not implemented
- Edge cases not handled
- Error scenarios ignored

**2. Unnecessary Additions**
- Features beyond specification
- Over-engineering
- Premature optimization

**3. Interpretation Gaps**
- Different understanding of requirements
- Assumptions not clarified
- Ambiguous specifications resolved incorrectly

---

## 7. Systematic Debugging

From `systematic-debugging/SKILL.md`, a methodical approach to fixing bugs that eliminates guesswork.

### Core Principle

**"NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST"**

This approach rejects symptomatic patching in favor of understanding underlying issues before attempting solutions.

**Key Insight:** Rushing toward fixes—especially under pressure—guarantees rework and new defects. Systematic investigation actually saves time compared to trial-and-error.

### The Four Mandatory Phases

#### Phase 1: Root Cause Investigation

**Objectives:**
- Thoroughly read error messages and stack traces
- Reproduce the issue reliably with documented steps
- Examine recent changes (commits, dependencies, configuration)
- Add diagnostic instrumentation at component boundaries
- Trace data flow backward to locate original source of bad values

**For Multi-Component Systems:**
- Instrument each boundary to identify where failures occur
- Don't assume the error location is the problem source
- Log data transformations at each stage

**Exit Criteria:** Understanding the problem's nature and origin

#### Phase 2: Pattern Analysis

**Objectives:**
- Locate similar working implementations in the codebase
- Study reference implementations completely, not selectively
- List all differences between working and broken code
- Document all dependencies, configuration, and assumptions

**Critical Practice:** Don't cherry-pick what seems relevant—study complete working examples to avoid missing hidden dependencies.

**Exit Criteria:** Clear identification of differences between working and broken patterns

#### Phase 3: Hypothesis Testing

**Objectives:**
- Form a specific, written hypothesis about root cause
- Test with minimal, isolated changes (one variable at a time)
- Verify results before proceeding
- Acknowledge knowledge gaps rather than guessing

**Testing Discipline:**
- Change only one thing at a time
- Document each hypothesis explicitly
- Verify results objectively
- Admit uncertainty rather than speculate

**Exit Criteria:** Validated hypothesis ready for implementation

#### Phase 4: Implementation

**Objectives:**
- Create a failing test case before fixing
- Implement a single fix addressing root cause
- Verify the fix resolves the issue
- Ensure no new breakage introduced

**TDD Integration:** Even during debugging, follow test-first principles.

**Exit Criteria:** Resolved issue with passing tests and no new failures

### Critical Thresholds and Decision Points

#### The Three-Fix Threshold

**Rule:** After two failed fix attempts, a third attempt triggers architectural review.

**Rationale:** Multiple fixes revealing different problems in different locations signals a flawed design, not isolated bugs.

**Action:** At this point, discussion about fundamental restructuring replaces additional fix attempts.

**What It Indicates:**
- Architecture doesn't support the requirement
- Design assumptions are invalid
- Component boundaries are wrong
- Deeper refactoring needed

### Red Flags Requiring Process Reset

These thinking patterns indicate deviation from systematic debugging:

- Proposing solutions before tracing data flow
- Attempting multiple simultaneous changes
- Skipping test creation
- Assuming understanding without verification
- Continuing fix attempts beyond the three-fix threshold
- "Let's try this and see if it works"
- "It might be this, or maybe that"

**When These Appear:** Return to Phase 1 for renewed investigation.

### Progress Verification

**After Phase 1:** Can you explain the problem's nature and origin?
**After Phase 2:** Have you identified concrete differences from working code?
**After Phase 3:** Do you have a testable, validated hypothesis?
**After Phase 4:** Does the issue no longer occur with tests passing?

---

## 8. Code Review Reception

From `receiving-code-review/SKILL.md`, principles for productively responding to feedback.

### Core Mindset

**"Verify before implementing. Ask before assuming. Technical correctness over social comfort."**

Don't accept feedback passively or performatively. Engage technically and verify applicability to your specific context.

### The Six-Step Process

1. **Read completely** without reacting
2. **Restate** requirements in your own words
3. **Check** against actual codebase conditions
4. **Evaluate** technical soundness for your specific stack
5. **Respond** with technical acknowledgment or reasoned objection
6. **Implement** one item at a time with testing

### Avoiding Performative Language

**Never use agreement theater.**

**Forbidden Phrases:**
- "You're absolutely right!"
- "Great point!" or "Excellent feedback!"
- Any expressions of gratitude or enthusiasm
- Excessive politeness

**Rationale:** "Actions speak. Just fix it. The code itself shows you heard the feedback."

**Instead, Use Factual Statements:**
- "Fixed. [Description]"
- "Implemented. [What changed]"
- Proceed directly to implementation

**Why This Matters:** Performative language wastes tokens, adds no technical value, and can mask lack of actual understanding.

### When Feedback Seems Unclear or Wrong

**Stop before implementing anything.**

**If Multiple Related Items Are Unclear:** Clarify first to prevent cascading errors.

**Push Back When Feedback:**
- Breaks existing functionality
- Lacks full context about the codebase
- Violates YAGNI principles (requesting unused features)
- Is technically incorrect for your specific stack
- Conflicts with established architectural decisions

**How to Push Back:**
- Use technical reasoning, not defensiveness
- Reference working code and tests
- Explain specific conflicts
- Propose alternatives with rationale
- Ask clarifying questions

**Example Good Pushback:**
```
This suggestion conflicts with the authentication architecture.
Current design uses JWT tokens (see auth/token.js:45).
Switching to sessions would require restructuring the API middleware.
Was that the intent, or should we keep the JWT approach?
```

**Example Bad Pushback:**
```
I don't think that's a good idea. The current way works fine.
```

### Verification Requirements

**Before Claiming Implementation:**
- Run the full test suite
- Verify the specific behavior mentioned in review
- Check for unintended side effects
- Confirm edge cases are handled

**Avoid:**
- "I think this addresses your concern"
- "This should fix it"
- "Probably done now"

**Use:**
- "Fixed. Tests pass. [Evidence]"
- "Implemented. Verified with [specific test]"

---

## 9. The Description Trap

A critical discovery from the superpowers development process about skill design.

### The Problem

**When skill descriptions summarize the workflow or process, agents follow the description instead of reading the full skill content.**

This undermines the entire purpose of skills, which is to provide detailed guidance beyond what fits in a short description.

### The Solution: Trigger-Only Descriptions

**Format:** "Use when [specific triggering conditions]"

**Characteristics of Effective Descriptions:**
- Written in third person
- Focus on problem symptoms rather than solutions
- Include concrete triggers agents would search for
- Maximum 1024 characters total
- **Avoid explaining how the skill works**

### Examples

**BAD - Process in Description:**
```yaml
description: Use when debugging. First investigate root cause, then analyze
patterns, test hypotheses, and implement fixes with tests.
```

**Problem:** Agent might follow this brief summary instead of the detailed four-phase process in the skill.

**GOOD - Trigger-Only:**
```yaml
description: Use when encountering bugs, errors, or unexpected behavior that
requires investigation and fixing.
```

**Why It Works:** Describes when to use the skill without summarizing how to use it.

### Technical Implementation

**YAML Frontmatter Format:**
```yaml
---
name: skill-name-with-hyphens
description: Use when [specific triggering conditions]
---
```

**Requirements:**
- **name:** Letters, numbers, and hyphens only (no parentheses or special characters)
- **description:** Maximum 1024 characters, trigger-only format

### Implications for Skill Design

**Do This:**
- Keep descriptions brief and trigger-focused
- Put all process details in the skill body
- Use concrete symptoms as triggers
- Make triggers searchable

**Don't Do This:**
- Summarize the workflow in the description
- Include step-by-step process
- Try to make description comprehensive
- Assume description replaces skill content

**Key Insight:** The description's purpose is skill discovery, not skill execution. Save execution details for the skill body.

---

## 10. Skills Architecture

### File Structure

Each skill is a directory containing at minimum a `SKILL.md` file:

```
skill-name/
  SKILL.md              # Required main skill file
  supporting-file.*     # Optional: only when needed
  reference.md          # Optional: heavy reference material
  scripts/              # Optional: reusable tools
```

### SKILL.md Format

**Required Components:**

1. **YAML Frontmatter** (mandatory)
2. **Skill Content** (methodology, process, principles)
3. **Optional Supporting References** (inline or external files)

**Example Structure:**
```markdown
---
name: systematic-debugging
description: Use when encountering bugs, errors, or unexpected behavior
that requires investigation and fixing.
---

# Systematic Debugging

## Core Principle
[Principle content here]

## The Four Mandatory Phases
[Process details here]

## Examples
[Examples here]
```

### When to Use Separate Files

**Self-Contained Skills:**
- Everything in a single SKILL.md file
- Content remains concise and focused
- Typically under 100 lines total

**Skills with Supporting Materials:**
Use separate files only when:
- Heavy reference material exceeds 100 lines
- Reusable tools or scripts require dedicated files
- API documentation needs comprehensive coverage
- Examples are extensive (50+ lines)

**Guideline from Documentation:**
> "Separate files for heavy reference (100+ lines), reusable tools, scripts, and utilities. Keep inline: principles, concepts, code patterns under 50 lines."

### Personal Skills and Shadowing

**Personal Skills Location:**
- Stored in user's personal skills directory
- Can override/shadow superpowers skills
- Same naming convention and structure

**Shadowing Mechanism:**
- Personal skill with same name takes precedence
- Allows customization without modifying core framework
- Enables team-specific or project-specific variations

**Use Cases:**
- Company-specific coding standards
- Project-specific workflows
- Team conventions
- Experimental skill variations

### Skill Categories

Based on the skills directory, 14 core skills:

1. **brainstorming** - Interactive design refinement
2. **dispatching-parallel-agents** - Multi-agent coordination
3. **executing-plans** - Plan implementation
4. **finishing-development-branch** - Branch completion
5. **receiving-code-review** - Feedback response
6. **requesting-code-review** - Review initiation
7. **subagent-driven-development** - Delegation workflows
8. **systematic-debugging** - Methodical bug fixing
9. **test-driven-development** - TDD enforcement
10. **using-git-worktrees** - Workspace management
11. **using-superpowers** - Meta-skill for framework usage
12. **verification-before-completion** - Evidence-based claims
13. **writing-plans** - Planning methodology
14. **writing-skills** - Skill creation guide

---

## 11. Key Takeaways for Integration

### Most Valuable Patterns for Other Projects

#### 1. The 1% Rule for Skill/Reference Checking

**Pattern:** If there's even a 1% chance a reference document, guideline, or skill applies, read it before proceeding.

**Why It Works:**
- Prevents costly assumptions
- Ensures current information (not memory)
- Catches edge cases
- Maintains consistency

**How to Implement:**
- Create clear trigger criteria for each reference
- Make checking non-negotiable in process
- Educate team on rationalizations to reject
- Build into workflow automation

**Application Beyond AI:**
- Code review checklists
- Security guidelines
- API documentation
- Architectural decision records

#### 2. Testing Iron Laws and Verification Requirements

**Pattern:** Absolute rules with no exceptions create clarity and prevent rationalization.

**Core Laws to Adopt:**
- No production code without failing test first
- No completion claims without verification evidence
- No fixes without root cause investigation

**Why It Works:**
- Eliminates debate about "when to skip"
- Creates clear success criteria
- Provides objective verification
- Prevents technical debt accumulation

**How to Implement:**
- Document iron laws explicitly
- Make violations immediately visible
- Automate enforcement where possible
- Include in code review standards

#### 3. Two-Stage Review (Spec Compliance → Code Quality)

**Pattern:** Separate specification compliance from code quality review.

**Why Order Matters:**
- Prevents wasting time reviewing wrong functionality
- Separates "what" from "how"
- Creates clear review criteria
- Enables specialized reviewers

**How to Implement:**
- First review: Does it meet requirements?
- Second review: Is it well-implemented?
- Same implementer fixes issues in both stages
- Don't proceed to stage 2 until stage 1 passes

**Application:**
- Pull request reviews
- Design reviews
- Documentation reviews
- API contract validation

#### 4. Persuasion Guardrails for Safety

**Pattern:** Use persuasive techniques to guide toward better outcomes.

**Key Techniques:**
- **Incremental validation:** 200-300 word sections with checkpoints
- **Choice architecture:** Multiple choice over open-ended
- **Sequential questioning:** One question at a time
- **YAGNI framing:** Position minimalism as discipline
- **Collaborative framing:** Shared ownership language

**Why It Works:**
- Reduces cognitive overload
- Catches misalignment early
- Makes decisions easier
- Builds buy-in incrementally

**How to Implement:**
- Break large decisions into smaller ones
- Validate assumptions frequently
- Provide structured choices
- Frame constraints positively

#### 5. Systematic Debugging Methodology

**Pattern:** Four mandatory phases before implementing fixes.

**The Phases:**
1. Root cause investigation (trace back to origin)
2. Pattern analysis (find working examples)
3. Hypothesis testing (one variable at a time)
4. Implementation (test first, then fix)

**Critical Threshold:** Three-fix rule triggers architectural review.

**Why It Works:**
- Eliminates guess-and-check
- Finds real problems, not symptoms
- Prevents fix-induced bugs
- Saves time overall

**How to Implement:**
- Require written hypothesis before fixes
- Track fix attempts per issue
- Trigger architecture review at threshold
- Include in debugging training

#### 6. The Description Trap Awareness

**Pattern:** Descriptions are for triggering, not for executing.

**Key Principle:** Keep execution details out of descriptions/summaries.

**Why It Matters:**
- Summaries replace detailed procedures
- Shortcuts undermine thoroughness
- Agents/humans follow brief version
- Details get ignored

**How to Implement:**
- Write trigger-only descriptions
- Put all process details in body
- Make descriptions searchable
- Test that descriptions don't replace content

**Application:**
- API documentation summaries
- Runbook descriptions
- Process document titles
- Commit message subjects

### Integration Checklist

When incorporating superpowers patterns into your project:

- [ ] Identify areas where systematic approaches would help
- [ ] Define iron laws for critical practices (testing, verification, debugging)
- [ ] Create skill-like reference documents with trigger-only descriptions
- [ ] Implement two-stage review for complex changes
- [ ] Add incremental validation checkpoints to large processes
- [ ] Document common rationalizations to reject
- [ ] Establish critical thresholds (like three-fix rule)
- [ ] Train team on persuasion guardrails
- [ ] Build verification requirements into workflows
- [ ] Create personal/team skills for project-specific needs

### Anti-Patterns to Avoid

Based on superpowers learnings:

- **Testing mocks instead of behavior**
- **Test-only methods in production code**
- **Mocking without understanding**
- **Incomplete mocks missing downstream fields**
- **Treating testing as optional follow-up**
- **Claiming completion without verification**
- **Fixing symptoms instead of root causes**
- **Continuing past three failed fix attempts**
- **Performative language in code review**
- **Process summaries replacing process details**

---

## 12. Technical Insights

### Token Efficiency

The framework is remarkably lightweight despite its comprehensive approach:

- Core documentation pulls in under 2k tokens
- Shell scripts fetch additional components as needed
- Complete planning-to-implementation cycles: ~100k tokens
- Sub-agents manage token-heavy implementation details

### Extensibility Mechanisms

**Skills with Graphviz Workflows:**
- Visual process diagrams as executable guidance
- Claude interprets diagrams for systematic problem-solving
- Enables visual documentation of complex workflows

**Modular Architecture:**
- Skills are composable and independent
- Commands extend CLI functionality
- Hooks provide integration points
- Agents define specialized roles

### Self-Updating Memory

The system maintains evolving notes that persist across sessions:
- Logs engagement and curiosity about projects
- Tracks project context and decisions
- Maintains continuity across long-running work
- Treats coding process holistically

### Installation and Usage

**Requirements:** Claude Code 2.0.13 or later

**Installation:**
```bash
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

**Auto-Discovery:** Skills are automatically discovered from the skills directory (though some users have reported issues with detection in version 3.6.2).

---

## 13. Community and Ecosystem

### Related Repositories

- **obra/superpowers** - Core skills library (10.1k stars)
- **obra/superpowers-skills** - Community-editable skills
- **obra/superpowers-marketplace** - Curated plugin marketplace

### Active Development

The project is under active development with regular updates. Recent activity includes:
- Issue tracking for skill discovery problems
- Community contributions to skills library
- Documentation improvements
- Platform compatibility updates

### Learning Resources

- **Simon Willison's Blog Post:** "Superpowers: How I'm using coding agents in October 2025" (https://simonwillison.net/2025/Oct/10/superpowers/)
- **Jesse Vincent's Blog:** "Superpowers: How I'm using coding agents" (https://blog.fsck.com/2025/10/09/superpowers/)
- **GitHub Discussions:** Active community sharing experiences and improvements

---

## 14. Conclusion

Superpowers represents a paradigm shift in AI-assisted coding from ad-hoc generation to systematic engineering. By encoding professional software development practices into enforceable skills, it enables agents to work with the discipline of experienced developers.

The framework's greatest strength is its uncompromising stance on quality fundamentals: tests before code, verification before completion, investigation before fixes, and evidence before claims. These iron laws prevent the shortcuts that lead to technical debt and brittle systems.

For teams and projects looking to integrate these patterns, the key lessons are clear:

1. **Make critical practices non-negotiable** through iron laws
2. **Use incremental validation** to catch issues early
3. **Separate specification from quality** in reviews
4. **Require evidence** for all success claims
5. **Systematize debugging** to eliminate guesswork
6. **Keep descriptions trigger-only** to prevent shortcut-taking

The superpowers framework demonstrates that structured workflows, far from constraining creativity, actually enable more ambitious autonomous work by providing clear guardrails and verification mechanisms.

---

## References and Additional Reading

### Primary Sources
- **Repository:** https://github.com/obra/superpowers
- **Community Skills:** https://github.com/obra/superpowers-skills
- **Marketplace:** https://github.com/obra/superpowers-marketplace

### Blog Posts and Articles
- Simon Willison: [Superpowers: How I'm using coding agents in October 2025](https://simonwillison.net/2025/Oct/10/superpowers/)
- Jesse Vincent: [Superpowers: How I'm using coding agents](https://blog.fsck.com/2025/10/09/superpowers/)

### Issue Tracking
- [Skills not discovered by Claude Code #151](https://github.com/obra/superpowers/issues/151)

### Release Notes
- [RELEASE-NOTES.md](https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md)

---

**Document Version:** 1.0
**Last Updated:** December 17, 2025
**Research By:** Technical Writer Agent
**License:** This research document is provided for educational purposes. The superpowers framework itself is MIT licensed.
