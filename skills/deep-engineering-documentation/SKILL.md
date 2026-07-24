---
name: deep-engineering-documentation
description: Produces exhaustive, source-grounded engineering documentation for a backend/API/controller/service — the kind used for mentor/senior-engineer review, not a README. Matches a rigorous per-endpoint template (Business Responsibilities, High-Level Architecture, Cross-Cutting Security, Exception Handling Strategy, Risks & Limitations, Manual Verification Items, Appendix diagrams). Trigger when the user asks for "engineering documentation," "technical documentation for my mentor," a deep dive on a controller/API/service, or attaches a sample/reference doc and asks for "one like this." Also trigger when the user wants every endpoint documented at API-Overview/Code-Flow/DB-Interactions/Security/Exception-Handling depth rather than a high-level summary. Do not use for simple API reference docs, OpenAPI specs, or short READMEs.
license: MIT
metadata:
  domain: documentation
  role: technical-writer
  scope: analysis-and-authoring
  output-format: docx
---

# Deep Engineering Documentation

## Why this is different from a normal doc-writing task

A README or API reference documents what an endpoint does. This skill produces something a senior engineer or mentor would trust as ground truth: every claim is traced to a specific file/function, ambiguities the codebase itself doesn't resolve are stated as open questions rather than papered over, and known risky patterns (silent failure, missing bounds checks, dead code paths) are called out explicitly. The output is long — often 25–40 pages for a system with 4–6 entry points — because depth, not brevity, is the point.

## Step 0: Pin down scope and format before writing anything

Ask (don't assume) if either is unclear:
- **Scope**: which controller(s)/service(s)/entry points get full depth? A large system may have near-duplicate entry points (test copies) or dead/unstarted code paths (present in source but never wired into the app) — confirm with the user whether to include, exclude, or footnote these rather than silently documenting or silently dropping them.
- **Format**: Word doc (.docx) is typical for this kind of deliverable; confirm before building.

**If the user attaches a sample/reference document and asks for "one like this," read the sample in full before writing a single line.** Extract its exact section list, section order, and — critically — the exact sub-heading structure used inside each per-endpoint section (e.g. API Overview / High-Level Flow / Detailed Code Flow / Database Interactions / Business Logic / Security & Validation / External Integrations / Exception Handling / Performance Notes / Response Structure / Summary). Matching this structure exactly, not approximately, is usually the actual deliverable requirement — a mentor comparing the two side by side will notice deviations like diagrams appearing inline in one but only in an appendix in the other.

## Step 1: Discover every entry point

Read the composition root (main()/app entrypoint) and enumerate every concurrently-running or routed entry point: HTTP routes, gRPC services, WebSocket handlers, raw TCP/UDP protocol servers, queue consumers. For each, note transport, port/path, and whether it's actually wired up and running (commented-out startup calls, unregistered routers, and orphaned files that are never imported are common and must be confirmed, not assumed).

## Step 2: Deep per-entry-point source trace

For each entry point in scope, trace it function-by-function and confirm, by reading the actual code (not by inferring from names):
- The full request/message flow from transport in to response/ACK out (or explicitly: no response, if that's what the code does).
- Every database/cache read and write, with the table/store name and when it fires.
- Business logic and derived behavior (validation rules, state machines, event derivation).
- Security: what authenticates the caller, what (if anything) authorizes the action, what's missing.
- External integrations (queues, event buses, other services).
- Exception handling: what happens on every failure path you can find (unknown identity, malformed input, downstream failure) — including cases where errors are silently swallowed or where the response doesn't reflect a real failure.
- Performance-relevant details (buffer sizes vs. protocol limits, N+1 patterns, uncached config reads, goroutine/thread lifecycle).

**When something can't be settled by reading alone** (e.g., whether a framework's routing layer actually reaches a handler the way its own conventions suggest, whether a library enforces an expiry check by default) — state this explicitly as a flagged, unresolved question rather than asserting it either way. This distinction (confirmed vs. flagged-for-verification) is what makes the document trustworthy; collapsing it into confident-sounding prose either way is the single biggest way this kind of document loses credibility.

For a system with several entry points, parallel research subagents (one per entry point) speed this up significantly — but recover and read their full output before proceeding; large findings frequently truncate in the tool result and require reading a persisted output file to recover in full.

## Step 3: Generate diagrams

One component diagram (all entry points → shared business logic → data stores → fan-out) plus one sequence diagram per entry point. If a mermaid renderer is available, use it. If not (no network access for mermaid-cli/cairosvg in a sandboxed environment is common), use `scripts/gen_diagrams_template.py` in this skill folder — a dependency-free matplotlib pattern for both diagram types that has been visually verified to render cleanly at typical page widths.

## Step 4: Assemble the document

Use `scripts/build_doc_template.js` (Node.js + the `docx` package) as the starting skeleton, or the `docx` skill's own conventions if preferred. Follow this section order exactly unless the user's sample specifies otherwise:

1. Header block (document type, system/controller name, module/scope, source file(s), document version, documentation scope, prepared-for, date)
2. System/Controller Overview
3. Business Responsibilities
4. High-Level Architecture (layer table)
5. External Integrations (table)
6. Persistence Overview
7. Endpoint/Entry-Point Summary (table)
8. API Documentation — one subsection per endpoint/entry point, each containing exactly: API Overview, High-Level Flow (prose, not a diagram — see below), Detailed Code Flow (numbered steps), Database Interactions (table), Business Logic, Security & Validation, External Integrations, Exception Handling (table), Performance Notes, Response Structure, Summary (ending with a pointer to the appendix diagram)
9. Cross-Cutting Runtime Architecture
10. Cross-Cutting Database Design
11. Cross-Cutting Security (Authentication / Authorization / Rate Limiting / Cryptographic Verification / Session Handling)
12. Exception Handling Strategy (consolidated table across all entry points)
13. Performance Considerations
14. Risks & Limitations (numbered)
15. Manual Verification Items (numbered — every flagged-not-confirmed item from Step 2, restated with exactly what to test)
16. Appendix (component diagram + every sequence diagram — diagrams live HERE ONLY, not inline in section 8)
17. Business Rules Reference (consolidated numbered list)
18. "End of Document."

**Diagram placement rule**: keep every diagram in the Appendix only. Do not embed the same image inline earlier in the document — that produces duplication a careful reader (or mentor doing a side-by-side comparison) will flag. Reference each with a one-line "See the Appendix for its sequence diagram" in that endpoint's Summary instead.

**Table-width discipline**: on a standard 12240-DXA-wide page with 720-DXA margins on each side, usable width is ~10800 DXA. Every table's column widths must sum to at or under this, or the rightmost column(s) render cut off. Check this before rendering, not after.

## Step 5: Visual QA

Convert the finished .docx to PDF (`soffice --headless --convert-to pdf`) and PDF pages to JPEG (`pdftoppm -jpeg`). Read (not just list) a sample covering: the cover/header page, at least one full per-endpoint page, every cross-cutting table page, and the appendix. Confirm no table overflows the margin and every image rendered (a missing/broken image reference will show as blank space or a build error — catch it here, not after delivery).

## Step 6: Final verification pass — do this even under time pressure

Before telling the user the document is ready, pick the 3–6 most consequential or surprising claims in the document (confirmed bugs, security gaps, panic risks — the things a mentor would zero in on) and re-check them directly against the source files yourself, even if the claims originated from earlier research (including subagent research). Quote the exact line(s) that confirm or refute the claim. This is the difference between "a document that describes the code" and "a document you can stand behind in a review" — do not skip it, and do not present it as done if you haven't actually done it.

## Step 7: Deliver

Present the .docx via the file-sharing mechanism available in your environment. Be ready to explain, plainly and honestly, what was ad hoc (scripts written for this one document) versus what's reusable (this skill) if asked about process.
