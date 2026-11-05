# Workflow Examples

Step-by-step walkthroughs that show skills working together on one task. [SKILLS_GUIDE.md](../SKILLS_GUIDE.md) lists
what each skill does. These files show the order to run them in, the prompt to type at each step, and the kind of
output to expect.

| Example                                                              | Scenario                                  | Skills used                                                              | Stack              |
| -------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------ | ------------------ |
| [Building a REST API from Scratch](REST_API_FROM_SCRATCH.md)         | New task API, from spec to a Docker image | `feature-forge`, `api-designer`, `golang-pro`, `test-master`, `devops-engineer` | Go                 |
| [Debugging a Production Issue](DEBUGGING_PRODUCTION_ISSUE.md)        | A slow Django endpoint in production      | `monitoring-expert`, `debugging-wizard`, `django-expert`, `test-master`  | Python, Django     |
| [Adding Authentication](ADDING_AUTHENTICATION.md)                    | JWT auth for an existing Spring Boot API  | `secure-code-guardian`, `spring-boot-engineer`, `test-master`, `security-reviewer` | Java, Spring Boot  |

## How to read an example

Each step gives the prompt to paste into Claude Code, names the skill that prompt triggers, and shows a short
output excerpt. Skill names are directory names under `skills/`, so you can open the matching `SKILL.md` and check
the workflow each step follows.

## How these examples were written

These are worked examples, not pasted session transcripts. Each step follows the Core Workflow in that skill's
`SKILL.md`, and the code excerpts use the framework versions listed in [CONTRIBUTING.md](../CONTRIBUTING.md). Run
the prompts in your own project and your wording and output will differ. That is expected. The prompts, the skill
order, and the checks at each step are the parts to copy.

One question from issue #98: where do the files a skill produces go? That is your team's call. Many teams commit
the spec from `feature-forge` with the code. Others turn the spec into tickets first and work one ticket per pull
request. Both work. Pick one and stay consistent.
