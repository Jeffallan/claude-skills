# Ontoly Workflow Reference

## Graph-First Analysis

Use Ontoly as the first source for software structure when its graph is present. The goal is not to avoid source files forever; the goal is to avoid repeated, lossy source search when a deterministic graph already contains the answer.

## Validation Checklist

1. Confirm graph location: `.ontoly/`, `SoftwareGraph.json`, diagnostics, validation reports, and graph hash.
2. Confirm freshness: build timestamp and repository path should match the current worktree.
3. Confirm quality: inspect diagnostics, coverage, trust, framework detection, and graph validation output.
4. Confirm scope: make sure the graph includes the packages, apps, or directories referenced by the user.
5. Confirm evidence: every answer should point to nodes, edges, source locations, or diagnostics.

## Query Selection

Use `ExplainArchitecture` for broad topology, `TraceExecution` for request flows, `FindDependencies` for direct dependency questions, `ImpactAnalysis` for refactors, `FindConfigurationUsage` for configuration, and `FrameworkReport` for framework-specific concepts.

## Fallback Rules

Search files only when the graph is missing, stale, incomplete, ambiguous, or contradicted by diagnostics. When falling back, limit source inspection to the smallest relevant area and report why graph evidence was insufficient.

