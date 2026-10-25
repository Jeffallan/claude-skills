# Project Setup and Runs

Use this reference when: Configuring an agent-qa project, authoring tests, validating files, executing a journey, or connecting MCP.

## Choose the existing project

Read project instructions and locate `agent-qa.config.yaml` before installing or initializing anything.
Use the package manager and runtime version already selected by the repository.
For another configuration file, pass `--config` explicitly rather than relying on the shell's working directory.
A saved-run review only needs the existing project and supported data readers; do not reinitialize it.

```bash
npx agent-qa --version
npx agent-qa --help
npx agent-qa --config ./agent-qa.config.yaml validate
```

The published 0.2.3 runtime requires Node.js 24 or newer.
If installation is part of the task, the npm setup is:

```bash
npm install -D agent-qa
```

For Claude or Codex subscription authentication, also install its sign-in plugin:

```bash
npm install -D @vostride/agent-qa-subscription-auth
```

API-key and compatible-endpoint setups do not require that subscription plugin.
Use the project's chosen provider; do not substitute a provider or invent an API key to get past a setup failure.
For a new project, inspect the current initialization choices:

```bash
npx agent-qa init --help
npx agent-qa auth --help
```

Initialize only the intended test project. Preserve its existing configuration when it already exists.
Use the documented credential flow; do not ask the user to paste credentials into chat or commit them in test files.
The [quickstart](https://vostride.com/docs/agent-qa/quickstart) explains initialization and model sign-in.

## Platform readiness

For web execution, install the browser required by the project when needed:

```bash
npx agent-qa install-browsers --chromium
```

Android and iOS execution use Appium with the appropriate device and driver setup.
Check the configured target and local device bindings before running a mobile test.
Do not invent device identifiers, app paths, or cloud-device credentials.
The [mobile guide](https://vostride.com/docs/agent-qa/guides/mobile-testing) covers UiAutomator2 and XCUITest setup.
Browser installation is not a prerequisite for reviewing already-recorded evidence.

## Author through the installed contract

Read the installed capability catalog and workspace posture before choosing an authoring operation:

```bash
npx agent-qa init --agent
npx agent-qa skills --json
```

The first command reports discovery metadata without initializing or changing the workspace.
The second locates the package's version-matched skills and schema references.
Read the packaged authoring guidance when exact fields, ID rules, or tool migrations matter.
Use an existing configured target key; preserve the user's stated values and acceptance criteria.

For a new test, call the connected `agent_qa_write_test` tool with its discovered schema.
For the stock example project's `komazon` target, an input is:

```json
{
  "intent": "Create a storefront test that verifies the product catalog is visible.",
  "scope": { "tier": "product", "key": "komazon" }
}
```

Use the actual target for a real application; the authoring scope is not an execution filter.
The host creates canonical IDs when it writes an entity. Do not invent an ID or copy another test's ID into a new file.
Read the written file, entity identity, verification disposition, and any refusal from the returned receipt.
A rejected draft is not an authored test. If a value-preservation check refuses the request, report the missing values rather than rephrasing around the check.
For an existing test, use `agent_qa_refine_test` with the current edit or verify action and the requested identity.
Its verify action evaluates the draft; it is not merely a text linter.
Authoring and verification can call models and execute tests. Respect an explicit request for a non-executing draft or read-only work.

For files already present, CLI validation and dry-run selection are additional non-execution checks.
The stock initializer provides this example file:

```bash
npx agent-qa validate tests/examples/komazon-checkout.yaml
npx agent-qa run tests/examples/komazon-checkout.yaml --dry-run
```

Neither command establishes that the browser journey passes, even if a dry run prints a run ID.
An unknown target or malformed existing test is a preparation problem to resolve through the supported authoring flow.
Do not weaken an expectation because the application fails it.

## Execute and retain identity

Prefer `agent_qa_start_run` when MCP is connected and execution is in scope.
Select files with `patterns`; the local 0.2.3 server rejects the advertised `scope` field for this tool.
When using the CLI, run the requested existing test:

```bash
npx agent-qa run tests/examples/komazon-checkout.yaml
```

Use an existing suite path when the requested scope spans a suite.
Keep the actual outcome and run ID from the command or supported run readers.
A process that has not finished is still in progress; a setup error is not an application failure.
Read the completed run's digest and relevant step evidence before reporting a result.
A later rerun has a different evidentiary scope; retain the earlier failure instead of silently replacing it.
See `evidence-and-memory.md` for the supported readers and correction workflow.

## Connect through MCP

An MCP client may launch the server outside the test project's directory.
Supply an absolute configuration path and keep it as one argument, including when it contains spaces:

```json
{
  "mcpServers": {
    "agent-qa": {
      "command": "npx",
      "args": ["-y", "agent-qa@0.2.3", "--config", "/absolute/project/agent-qa.config.yaml", "mcp"]
    }
  }
}
```

Replace the example path with the intended project configuration.
Install and configure the project's model and optional authentication plugin before requesting execution.
For execution-capable tools, configure the client's tool-call timeout for the expected test or suite duration.
The [coding-agent guide](https://vostride.com/docs/agent-qa/coding-agents) uses 100 minutes for a default single test; larger suites may need more.
Discover tools from the connected server; use their returned schemas instead of guessing argument names.
`agent_qa_write_test` can author and verify a test, so treat it as execution-capable work, not a read-only query.
`agent_qa_start_run` acknowledges a run; inspect its returned identity and follow completion through supported readers or streams.
If only completed-run listing is available, an absent entry does not prove the run failed or never started.
Avoid starting duplicate runs while the original is still active or its state is unknown.

## Finish gate

Report preparation checks separately from execution results.
For an execution request, include the actual run outcome and evidence, or the concrete condition that prevented it.
For authoring work, report the actual written artifact and any verification performed by the authoring tool.
If the user explicitly forbids execution, do not invoke an authoring operation that runs tests; provide the proposed intent and explain that limitation.
