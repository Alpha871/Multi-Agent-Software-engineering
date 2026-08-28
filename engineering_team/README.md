# Engineering Team — Multi-Agent Software Crew

A CrewAI crew that turns a plain-English requirement into a working, tested Python
application. Four role-specialised agents run in sequence — a lead designs the system, a
backend engineer implements it, a frontend engineer builds a Gradio UI, and a test
engineer writes and runs unit tests until they pass. All generated code is written and
executed inside a sandbox, never on your machine directly.

All commands below are run from the `engineering_team` directory.

## Pipeline

```
requirements (main.py)
      │
      ▼
engineering_lead      design_task     ──>  sandbox/design.md
  gpt-5.5                                  (markdown design, signatures only, no code)
  + Context7 MCP                           checks live Gradio 6 APIs
      │
      ▼
backend_engineer      code_task       ──>  sandbox/backend.py
  + sandbox tools                          stdlib only, no third-party imports
      │
      ▼
frontend_engineer     frontend_task   ──>  sandbox/app.py + sandbox/_validate.py
  + sandbox tools                          Gradio UI, validated without .launch()
  + Context7 MCP
      │
      ▼
test_engineer         test_task       ──>  sandbox/test_backend.py
  + sandbox tools                          sandbox/test_summary.md
                                           unittest, fixed and rerun until green
```

Each engineer has four tools: list, read and write files in `sandbox/`, and run a Python
file there **inside an ephemeral Docker container**. Tool result caching is disabled, so
agents always see the current state of the sandbox rather than a stale copy.

## 1. Prerequisites

| Requirement | Why |
| --- | --- |
| Python 3.10–3.13 (3.13 pinned) | The crew runtime |
| [uv](https://docs.astral.sh/uv/) | Dependencies, and initialising the sandbox project |
| **Docker, running** | Every agent-generated script executes in a throwaway container |
| `crewai` CLI | `crewai run` is the entry point |

Docker is not optional: `run_sandbox_python` shells out to
`docker run --rm ... ghcr.io/astral-sh/uv:python3.13-bookworm-slim`. If the Docker daemon
is not up, the engineers can write code but never verify it.

## 2. Install dependencies

```bash
uv sync
```

or, equivalently, `crewai install`.

## 3. Configure API keys

Create a `.env` file **in this directory** (it is gitignored):

```bash
OPENAI_API_KEY=sk-...          # engineering_lead (gpt-5.5)
OPENROUTER_API_KEY=sk-or-...   # the three engineers (nvidia/nemotron-3-ultra, free tier)
```

Both are required with the default configuration. To run everything on one provider,
change the `llm:` lines in `src/engineering_team/config/agents.yaml` — see step 6.

## 4. Set the requirements

The task the crew builds is a plain string in `src/engineering_team/main.py`:

```python
requirements = """
A simple account management system for a trading simulation platform.
...
"""
```

Replace it with whatever you want built. Keep it to something a single module can hold —
the crew has no directory structure and only the Python standard library plus Gradio.

## 5. Run the crew

```bash
crewai run
```

This wipes `sandbox/`, re-initialises it as a fresh uv project with Gradio, then runs the
four tasks in order. Expect several minutes; the test engineer loops until its tests pass.

Output lands in `sandbox/`:

| File | Written by |
| --- | --- |
| `design.md` | engineering_lead |
| `backend.py` | backend_engineer |
| `app.py`, `_validate.py` | frontend_engineer |
| `test_backend.py`, `test_summary.md` | test_engineer |

### Run what the crew built

```bash
cd sandbox
uv run app.py            # the Gradio UI
uv run -m unittest test_backend -v
```

## 6. Customising

| Change | Where |
| --- | --- |
| Agent roles, goals, models | `src/engineering_team/config/agents.yaml` |
| Task descriptions and outputs | `src/engineering_team/config/tasks.yaml` |
| Add or remove agents, tasks, tools | `src/engineering_team/crew.py` |
| Sandbox tools and Docker image | `src/engineering_team/tools/sandbox_tools.py` |
| The requirement being built | `src/engineering_team/main.py` |

**Swapping models.** Each agent has its own `llm:` key in `agents.yaml`, so you can mix
providers freely — `openai/gpt-5.5`, `openrouter/<vendor>/<model>`, and so on. The
`sandbox_gpt/`, `sandbox_claude/` and `sandbox_mixed/` directories are saved output from
running the same requirement under different model configurations, kept for comparison.

**Turning off tracing.** `crew.py` sets `tracing=True`. Set it to `False` if you do not
want runs sent to CrewAI's tracing service.

## The Context7 patch

`src/engineering_team/patch.py` is imported for its side effect before the crew starts. It
works around a bug in CrewAI 1.14.4: HTTPS MCP tool names are sanitised on discovery, but
the sanitised name is then sent back to the server, so any tool with a hyphen in its name
— such as Context7's `resolve-library-id` — is unreachable. The patch preserves the
original server-side name on the wrapper.

Re-check whether this is still needed after upgrading CrewAI; if the upstream bug is
fixed, delete `patch.py` and its import in `main.py`.

## Troubleshooting

**`Cannot connect to the Docker daemon`**
Start Docker Desktop. Every `run_sandbox_python` call needs it.

**The frontend task hangs until timeout**
The validation script called `.launch()`. It must only import and construct the Blocks
object — this is stated in `tasks.yaml`, but a model occasionally ignores it.

**An engineer imports a third-party package**
Only the standard library (plus Gradio, for the frontend) is available in the sandbox. The
constraint is in each agent's `goal` in `agents.yaml`; tighten the wording if it drifts.

**`sandbox/` was wiped and I wanted to keep it**
`reset_sandbox()` runs at the start of every `crewai run`. Copy the directory aside first,
the way `sandbox_gpt/` and friends were kept.
