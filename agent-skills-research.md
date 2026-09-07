# Skill-aware `execute_tool` instrumentation

Research and design notes for client-side skill tool execution. Checked against
public documentation on 2026-09-06.

## Scope

This design covers tool calls executed by an agent SDK or application runtime.
It does not cover:

- hosted skill execution hidden behind a model or agent service;
- skill registration, discovery, and configuration metadata other than the
  source URI retained by the runtime;
- inferring which skill motivated an unrelated later tool call.

## Principles

- Skill tool executions refine the existing `execute_tool` span.
- A refinement is used when a framework exposes enough runtime information to
  identify the specialized operation. Otherwise, use the generic tool span.
- Refinements provide a more useful span name. Every dynamic span-name value is
  also recorded as an attribute.
- Skill association comes from tool arguments, tool definitions, or framework
  state. It is not inferred from prompts, arbitrary command text, or an earlier
  skill activation.
- Command execution is not inherently skill-related. A command span carries
  skill attributes only when the framework explicitly associates the execution
  with a skill.
- Process information reuses the CLI semantic conventions. Singular process
  attributes apply to the tool span only when it directly represents one known
  process. Otherwise, process executions are represented by CLI child spans.
- Catalog identity, distribution, and trust metadata belongs to discovery and
  configuration. It applies to `execute_tool` only when the runtime preserves
  an explicit association with the catalog entry.

## Attributes

| Attribute | Applies when | Source |
|---|---|---|
| `gen_ai.skill.description` | The execution resolves to a skill with an available description | Resolved skill state |
| `gen_ai.skill.name` | The tool call or framework explicitly identifies a skill | Tool argument, tool definition, or registered framework state |
| `gen_ai.skill.resource.name` | The tool directly reads or executes a named skill resource | Logical skill-relative resource argument or framework state |
| `gen_ai.skill.source.uri` | The execution resolves to a skill whose original loader URI is available | Resolved skill state |

`gen_ai.skill.resource.name` is a logical identifier:

```text
Tool argument:          references/output-format.md
Resolved filesystem:   /tmp/skills/report/references/output-format.md
Recorded value:        references/output-format.md
```

Instrumentation must not record the resolved absolute path or derive the value
from arbitrary command text.

## Span refinements

### Load skill

```yaml
id: gen_ai.execute_tool.load_skill.internal
ref: gen_ai.execute_tool.internal
span_name: "{gen_ai.tool.name} {gen_ai.skill.name}"
conditionally_required:
  - gen_ai.skill.name: when available
```

```text
load_skill code-review
  gen_ai.operation.name    = "execute_tool"
  gen_ai.tool.name         = "load_skill"
  gen_ai.skill.name        = "code-review"
  gen_ai.skill.description = "Review code using the team's review policy."
  gen_ai.skill.source.uri  = "file:///opt/skills/code-review"
```

### Read skill resource

```yaml
id: gen_ai.execute_tool.read_skill_resource.internal
ref: gen_ai.execute_tool.internal
span_name: "{gen_ai.tool.name} {gen_ai.skill.name} {gen_ai.skill.resource.name}"
conditionally_required:
  - gen_ai.skill.name: when available
  - gen_ai.skill.resource.name: when available
```

```text
load_skill_resource code-review references/rules.md
  gen_ai.operation.name          = "execute_tool"
  gen_ai.tool.name               = "load_skill_resource"
  gen_ai.skill.name              = "code-review"
  gen_ai.skill.resource.name     = "references/rules.md"
```

### Execute command

```yaml
id: gen_ai.execute_tool.command.internal
ref: gen_ai.execute_tool.internal
span_name: "{gen_ai.tool.name}"
executable_span_name: "{gen_ai.tool.name} {process.executable.name}"
skill_resource_span_name: >
  {gen_ai.tool.name} {gen_ai.skill.name} {gen_ai.skill.resource.name}
skill_executable_span_name: >
  {gen_ai.tool.name} {gen_ai.skill.name} {process.executable.name}
```

```text
shell
  gen_ai.operation.name = "execute_tool"
  gen_ai.tool.name      = "shell"
```

```text
run_skill_script code-review scripts/check.py
  gen_ai.operation.name          = "execute_tool"
  gen_ai.tool.name               = "run_skill_script"
  gen_ai.skill.name              = "code-review"
  gen_ai.skill.resource.name     = "scripts/check.py"
```

## Commands and CLI processes

The tool span covers framework work such as argument validation, skill
resolution, approval, hooks, retries, and result normalization. CLI spans cover
the processes started by the tool.

```text
shell                                      INTERNAL execute_tool
├─ bash                                    CLIENT CLI
│  process.executable.name = "bash"
│  process.executable.path = "/bin/bash"
│  process.exit.code       = 0
└─ python                                  CLIENT CLI
   process.executable.name = "python"
   process.executable.path = "/usr/bin/python"
   process.exit.code       = 0
```

The command refinement may reuse these attributes on the tool span when one
process represents the whole tool execution:

| CLI attribute | Tool-span requirement |
|---|---|
| `process.executable.name` | Required when one process is directly executed and its name is available |
| `process.executable.path` | Recommended when one process is directly executed and its path is available |
| `process.exit.code` | Required when the tool reports one exit code |

`process.command_args` is not populated from a shell command string. It can be
used on a CLI child span when the actual argv is available and sanitized.

See [OpenTelemetry CLI span conventions](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/cli/cli-spans.md).

## Metrics

There are no skill-specific metric refinements. The main
`gen_ai.execute_tool.duration` metric may include:

```text
gen_ai.skill.name
gen_ai.skill.resource.name
```

They are recorded only when the association is explicit and the value set is
expected to be bounded.

## Framework mapping

| Framework | Tool call | Mapping | Skill attributes |
|---|---|---|---|
| Google ADK | `load_skill(skill_name)` | Load skill | Skill name |
| Google ADK | `load_skill_resource(skill_name, file_path)` | Read skill resource | Skill and resource |
| Google ADK | `run_skill_script(skill_name, file_path, ...)` | Execute command | Skill and resource |
| Microsoft Agent Framework | `load_skill`, `read_skill_resource`, `run_skill_script` | Same as ADK | Explicitly available |
| OpenAI Agents lazy sandbox | `load_skill(skill_name)` | Load skill | Skill name |
| OpenAI Agents | `shell(commands)` or `exec_command(command)` | Execute command | Usually none |
| LangChain Deep Agents | `read_file(.../SKILL.md)` | Load skill only when resolved through configured skill roots | Skill name |
| LangChain Deep Agents | `read_file(.../<resource>)` | Read resource only when resolved through configured skill roots | Skill and resource |
| LangChain Deep Agents | `execute(command)` | Execute command | Usually none |
| Pydantic AI | `load_capability(id)` | Load skill only when registry state confirms a `Skills` capability | Skill name |
| Claude Agent SDK | Built-in `Skill` tool | Load skill | Skill name |
| Strands Agents | `skills(skill_name)` | Load skill | Skill name |
| Agno | `get_skill_instructions(skill_name)` | Load skill | Skill name |
| Agno | `get_skill_reference` or `get_skill_script(execute=false)` | Read skill resource | Skill and resource |
| Agno | `get_skill_script(execute=true)` | Execute command | Skill and resource |
| GitHub Copilot SDK eager skills | No tool call | Outside scope | None |

Important distinctions:

- Agno's `get_skill_script` reads by default and executes only when
  `execute=true`.
- OpenAI `shell` may have mounted skills, but the command call usually does not
  identify which skill motivated it.
- A Deep Agents filesystem call is skill-aware only when instrumentation can
  resolve the path using middleware or backend configuration.
- Pydantic's `load_capability` also loads non-skill capabilities, so tool-name
  matching is insufficient.

### Command and skill-script tool parameters

Skill scripts commonly use the same tool as general commands. A dedicated
skill-script tool maps to command execution only when its runner executes a
command or process.

| Framework | Tool | Model-visible parameters | Use |
|---|---|---|---|
| [OpenAI Agents](https://openai.github.io/openai-agents-python/sandbox/guide/) | `exec_command` | `cmd`; optional `workdir`, `shell`, `login`, `tty`, `yield_time_ms`, `max_output_tokens` | General commands and scripts from materialized skills |
| [LangChain Deep Agents](https://docs.langchain.com/oss/python/deepagents/sandboxes) | `execute` | `command` | General commands and skill scripts in a sandbox |
| [Strands Agents](https://strandsagents.com/docs/user-guide/concepts/plugins/skills/) | `shell` | `command` (string, list, or command objects); optional `parallel`, `ignore_errors`, `timeout`, `work_dir` | General commands and bundled skill scripts |
| [Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool#parameters) | `bash` | `command`, or optional `restart: true` | General commands; client executes them |
| [Google ADK](https://github.com/google/adk-python/blob/main/src/google/adk/tools/skill_toolset.py) | `run_skill_script` | `skill_name`, `file_path`; executor-specific `command`, or optional `args`, `short_options`, `positional_args` | Dedicated skill-script execution |
| [Microsoft Agent Framework](https://github.com/microsoft/agent-framework/blob/main/python/packages/core/agent_framework/_skills.py) | `run_skill_script` | `skill_name`, `script_name`, optional `args` | Dedicated skill-script execution; the application supplies the runner for file scripts |
| [Agno](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/skills/agent_skills.py) | `get_skill_script` | `skill_name`; optional `script_path`, `execute`, `args`, `timeout` | Reads by default; executes the skill script when `execute=true` |

## AI Catalog

The draft [AI Catalog specification](https://ai-catalog.io/spec/) is a discovery
container for skills and other AI artifacts. It is not a skill execution API.

```json
{
  "identifier": "urn:air:example.com:skill:code-review",
  "type": "application/agent-skills+zip",
  "url": "https://skills.example.com/code-review/skill.zip",
  "version": "1.2.0"
}
```

| Catalog field | Meaning | `execute_tool` consequence |
|---|---|---|
| `identifier` | Stable artifact identity | Not interchangeable with `gen_ai.skill.name`; unavailable unless the runtime retains the catalog association |
| `type` | Artifact media type, including Agent Skills JSON, Markdown, ZIP, or gzip | Selects the artifact format, not a skill resource type |
| `url` or `data` | Artifact distribution reference or inline content | Not the executed resource name or necessarily the runtime source |
| `displayName`, `description` | Listing metadata that may override native metadata for display | Not tool-execution attributes |
| `version` | Catalog artifact version | Available only if selection metadata survives into execution |
| `publisher`, `trustManifest` | Publisher and trust metadata | Discovery and verification concerns, outside `execute_tool` |

```text
load_skill("code-review")
  gen_ai.skill.name = "code-review"

# Do not infer identifier, URL, or version unless the runtime carries the
# selected catalog entry into this execution boundary.
```

## Reference scenarios

The repository scenarios demonstrate values available at real SDK boundaries:

| Scenario | Coverage |
|---|---|
| `reference/scenarios/google-adk` | Skill load, reference read, asset read, and skill script execution |
| `reference/scenarios/openai-agents` | Local `ShellTool` execution and structured command result |

Runnable exploratory applications are under `test_apps/`.

## Deferred

| Property or behavior | Reason |
|---|---|
| Skill resource type | Usually inferred from directory layout or tool names |
| Skill operation attribute | Duplicates the tool identity for specialized calls |
| Skill-specific metrics | Main execute-tool duration metric already carries bounded skill attributes |
| Skill instructions | Large, redundant, and potentially sensitive |
| Skill version | No common field across skill formats and frameworks |
| Catalog identifier, type, or version | Discovery metadata with no common runtime association |
| Catalog publisher or trust metadata | Outside tool execution |
| Propagation to later tools | Most frameworks expose no reliable causal association |

## Public references

- [Google ADK skills](https://adk.dev/skills/)
- [Microsoft Agent Framework skills](https://learn.microsoft.com/en-us/agent-framework/agents/skills)
- [OpenAI Agents SDK tools](https://openai.github.io/openai-agents-python/tools/)
- [LangChain Deep Agents skills](https://docs.langchain.com/oss/python/deepagents/skills)
- [Pydantic AI Harness skills](https://pydantic.dev/docs/ai/harness/skills/)
- [Claude Agent SDK skills](https://code.claude.com/docs/en/agent-sdk/skills)
- [Strands Agent Skills](https://strandsagents.com/docs/user-guide/concepts/plugins/skills/)
- [Agno skills](https://docs.agno.com/skills/overview)
- [Agent Skills specification](https://agentskills.io/specification)
- [AI Catalog specification](https://ai-catalog.io/spec/)
