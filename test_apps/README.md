# Skill telemetry test apps

Small apps for inspecting the telemetry produced when an agent discovers, loads,
and executes a local Agent Skill.

Both apps use the OpenTelemetry distro and export spans over OTLP/gRPC to
`http://localhost:4317`. Content capture is enabled explicitly and may include
prompts, tool arguments, tool results, and skill content. Use only test data.

## Google ADK

Uses ADK's native agent, model, and tool telemetry. ADK 2.8.0 caps the
OpenTelemetry API at 1.42.1, so this app uses the newest compatible distro.
The separately released Google GenAI instrumentation currently requires 1.43+
and cannot be installed with this ADK release.

```bash
cd test_apps/google_adk_skills
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY.
uv sync
uv run --env-file .env opentelemetry-instrument python app.py
```

Override the default model with `MODEL`, or the prompt with `PROMPT`.

### Google ADK local variations

`variations_app.py` sends a separate request for every selected scenario:

| Scenario | Calls exercised |
|---|---|
| `catalog` | `list_skills` |
| `load` | `load_skill` |
| `reload` | repeated `load_skill` |
| `reference` | `load_skill`, `load_skill_resource` for a reference |
| `asset` | `load_skill`, `load_skill_resource` for an asset |
| `script-code-executor` | `run_skill_script` with structured arguments |
| `script-environment` | `run_skill_script` with a shell command |
| `registry` | `search_skills`, registry-backed load and script execution |
| `additional-tool` | skill activation followed by ordinary `format_sum` |
| `missing-resource` | resource lookup error |
| `missing-script` | script lookup error |

```bash
SCENARIOS=all uv run --env-file .env opentelemetry-instrument python variations_app.py

SCENARIOS=reference,script-environment uv run --env-file .env \
  opentelemetry-instrument python variations_app.py
```

The registry scenario uses an in-memory `SkillRegistry`. It exercises the same
model-facing discovery and loading calls without requiring a cloud registry.

## OpenAI Agents SDK

Uses a `SandboxAgent`, lazy local skills, and `UnixLocalSandboxClient`. This
client runs commands on the local machine in a temporary workspace, so only use
trusted skills and scripts.

```bash
cd test_apps/openai_agents_skills
cp .env.example .env
# Edit .env and set OPENAI_API_KEY.
uv sync
uv run --env-file .env opentelemetry-instrument python app.py
```

### Local OpenAI variations

`app.py` accepts these `SKILL_SOURCE` values:

| Value | Skill materialization | Model-facing tools |
|---|---|---|
| `lazy` | Local directory, copied on demand | `load_skill`, then `exec_command` |
| `eager-dir` | Local directory, copied before the request | `exec_command` |
| `inline` | `Skill` object assembled in application code | `exec_command` |
| `git` | Git repository cloned into the local sandbox | `exec_command` |

```bash
SKILL_SOURCE=eager-dir uv run --env-file .env opentelemetry-instrument python app.py
SKILL_SOURCE=inline uv run --env-file .env opentelemetry-instrument python app.py
```

For `git`, set `SKILL_GIT_REPO`, `SKILL_GIT_REF`, and optionally
`SKILL_GIT_SUBPATH`.

With the lazy source, `SCENARIO=reload` exercises the `already_loaded` result
and `SCENARIO=interactive` exercises `exec_command` plus `write_stdin`:

```bash
SCENARIO=reload uv run --env-file .env opentelemetry-instrument python app.py
SCENARIO=interactive uv run --env-file .env opentelemetry-instrument python app.py
```

`local_shell_app.py` covers the native OpenAI `ShellTool` with a local executor.
Its executor receives a call ID, command list, timeout, output limit, status,
raw provider payload, and run context.

```bash
uv run --env-file .env opentelemetry-instrument python local_shell_app.py
```

### Dashboard-hosted OpenAI skill

Create a hosted skill with the OpenAI Skills API. If your account exposes a
Skills UI in the dashboard, you can use that instead. Put the resulting skill
ID and a prompt in `.env`:

```python
from pathlib import Path
from openai import OpenAI

with Path("my-skill.zip").open("rb") as bundle:
    skill = OpenAI().skills.create(
        files=[("my-skill.zip", bundle, "application/zip")]
    )
print(skill.id)
```

```dotenv
OPENAI_SKILL_ID=skill_...
# Pin a version or omit it to use the skill's default version.
OPENAI_SKILL_VERSION=1
PROMPT=Use the configured skill to perform a task.
```

Run the hosted variant:

```bash
uv run --env-file .env opentelemetry-instrument python hosted_skill_app.py
```

This uses a hosted `shell` tool with a `container_auto` environment. OpenAI
loads and executes the skill remotely. This is intentionally different from
`app.py`, where the Agents SDK executes skill tools through a local sandbox.

The Agents SDK also keeps its built-in OpenAI trace exporter enabled. The
OpenTelemetry Agents instrumentor consumes the same SDK trace callbacks.

## Pinned versions

The test apps pin these versions:

| Package | Version |
|---|---:|
| `google-adk` | `2.8.0` |
| `openai-agents` | `0.22.0` |
| `opentelemetry-distro` (ADK, newest compatible) | `0.63b0` |
| `opentelemetry-distro` (OpenAI) | `0.65b0` |
| `opentelemetry-instrumentation-genai-openai` | `1.1b0` |
| `opentelemetry-instrumentation-genai-openai-agents` | [`main` at `59e6efe`](https://github.com/open-telemetry/opentelemetry-python-genai/commit/59e6efe6c0be45a9da78f8f3c21c5d6ac4488ed1) |

References:

- [Google ADK Skills](https://adk.dev/skills/)
- [Google ADK traces](https://adk.dev/observability/traces/)
- [Google ADK content capture](https://adk.dev/observability/logging/#capture-prompt-content)
- [OpenAI Agents SDK sandbox skills](https://openai.github.io/openai-agents-python/sandbox/guide/#capabilities)
- [OpenAI Skills REST API](https://developers.openai.com/api/reference/python/resources/skills/methods/create)
- [OpenAI hosted container skill references](https://developers.openai.com/api/reference/cli/resources/containers/methods/create)
- [Google GenAI OpenTelemetry instrumentation](https://pypi.org/project/opentelemetry-instrumentation-google-genai/)
- [OpenAI OpenTelemetry instrumentation](https://pypi.org/project/opentelemetry-instrumentation-genai-openai/)
- [OpenAI Agents OpenTelemetry instrumentation](https://pypi.org/project/opentelemetry-instrumentation-genai-openai-agents/)
