# GenAI semconv issue/PR triage

Snapshot: 2026-08-28. Scope: all open issues, all open PRs, all closed-not-merged PRs
in `open-telemetry/semantic-conventions-genai`. Duplicates are combined into one row.

Repo shorthand: bare `#N` links to this repo. Upstream refers to
`open-telemetry/semantic-conventions`.

## v1 (stable) scope

Target for stabilization: **agentic frameworks and inference libraries**. Harnesses,
protocols, and platform/governance areas are explicitly post-v1.

In scope:
- shape decisions that cannot be redone without breaking (span/metric taxonomy,
  metric shape, content schema),
- breaking changes that must land before stable,
- bugs and clarifications on already-shipped conventions,
- features without which agentic observability does not work.

`discuss`: the in/out call depends on a decision we have not made yet - see the
notes under each such row's topic.

Out of scope (empty cell): anything that can be added additively later, new areas,
and breaking changes that are not important enough to block v1. A second major
bump within a year is assumed, so non-essential churn can wait.

---

## Categories

- **0. Modeling / structural design change** - changes the shape of the model
  (span/metric naming, taxonomy, what is a span vs a metric).
- **1. Non-structural breaking change** - rename, requirement-level change,
  clarification that invalidates existing instrumentation.
- **2. Feature missing from existing conventions** - additive, fits the current model.
  Rated by importance for observability and size.
- **3. New area** - a domain the conventions do not cover at all.

Excluded as infra/meta: #84, #106, #166, #182, #204, #233, #247, #276, #281, #297, #315,
#290, #282, #158, #155, #183, #112, #273, #441, #444, #472, and all dependency bumps
(#292, #328, #366, #397, #429, #432, #434).

---

## 0. Modeling / structural design change

| Topic | Items | In v1 scope |
|---|---|---|
| Operation naming model | [#21](https://github.com/open-telemetry/semantic-conventions-genai/issues/21), [#20](https://github.com/open-telemetry/semantic-conventions-genai/issues/20), [#355](https://github.com/open-telemetry/semantic-conventions-genai/pull/355) | in scope |
| Span/metric definition principles | [#249](https://github.com/open-telemetry/semantic-conventions-genai/issues/249) | in scope |
| Client metric set + token usage metric shape | [#101](https://github.com/open-telemetry/semantic-conventions-genai/issues/101), [#76](https://github.com/open-telemetry/semantic-conventions-genai/issues/76), [#23](https://github.com/open-telemetry/semantic-conventions-genai/issues/23), [#19](https://github.com/open-telemetry/semantic-conventions-genai/issues/19), [#374](https://github.com/open-telemetry/semantic-conventions-genai/pull/374), [#197](https://github.com/open-telemetry/semantic-conventions-genai/pull/197), [#96](https://github.com/open-telemetry/semantic-conventions-genai/pull/96) | in scope |
| Count operations or attempts; metric scope | [#476](https://github.com/open-telemetry/semantic-conventions-genai/issues/476), [#215](https://github.com/open-telemetry/semantic-conventions-genai/pull/215) | in scope |
| Agent vs workflow vs node taxonomy | [#477](https://github.com/open-telemetry/semantic-conventions-genai/issues/477), [#264](https://github.com/open-telemetry/semantic-conventions-genai/issues/264), [#187](https://github.com/open-telemetry/semantic-conventions-genai/issues/187), [#318](https://github.com/open-telemetry/semantic-conventions-genai/issues/318), [#243](https://github.com/open-telemetry/semantic-conventions-genai/issues/243), [#35](https://github.com/open-telemetry/semantic-conventions-genai/issues/35), [#37](https://github.com/open-telemetry/semantic-conventions-genai/issues/37), [#11](https://github.com/open-telemetry/semantic-conventions-genai/issues/11), [#24](https://github.com/open-telemetry/semantic-conventions-genai/issues/24) | in scope |
| Client vs server invoke_agent, duplicate spans, entry span | [#252](https://github.com/open-telemetry/semantic-conventions-genai/pull/252), [#308](https://github.com/open-telemetry/semantic-conventions-genai/issues/308), [#302](https://github.com/open-telemetry/semantic-conventions-genai/issues/302), [#475](https://github.com/open-telemetry/semantic-conventions-genai/pull/475) | in scope |
| Part base class / schema nullability | [#59](https://github.com/open-telemetry/semantic-conventions-genai/issues/59), [#53](https://github.com/open-telemetry/semantic-conventions-genai/issues/53), [#454](https://github.com/open-telemetry/semantic-conventions-genai/pull/454) | in scope |
| MCP: params/result for sampling, elicitation, completion | [#66](https://github.com/open-telemetry/semantic-conventions-genai/issues/66) | discuss |

## 1. Non-structural breaking change

| Topic | Items | In v1 scope |
|---|---|---|
| Deprecate per-message finish_reason | [#362](https://github.com/open-telemetry/semantic-conventions-genai/issues/362), [#471](https://github.com/open-telemetry/semantic-conventions-genai/issues/471), [#363](https://github.com/open-telemetry/semantic-conventions-genai/pull/363) | in scope |
| MCP error.type / status code / session-duration metric | [#313](https://github.com/open-telemetry/semantic-conventions-genai/issues/313), [#312](https://github.com/open-telemetry/semantic-conventions-genai/issues/312), [#314](https://github.com/open-telemetry/semantic-conventions-genai/issues/314), [#452](https://github.com/open-telemetry/semantic-conventions-genai/pull/452), [#458](https://github.com/open-telemetry/semantic-conventions-genai/pull/458), [#453](https://github.com/open-telemetry/semantic-conventions-genai/pull/453) | discuss |
| Failed-operation content capture | [#459](https://github.com/open-telemetry/semantic-conventions-genai/pull/459) | in scope |
| Role for tool_call_response messages | [#141](https://github.com/open-telemetry/semantic-conventions-genai/issues/141) | in scope |
| System instructions shape in scenarios | [#360](https://github.com/open-telemetry/semantic-conventions-genai/issues/360) | in scope |
| Memory records vs retrieval documents boundary | [#139](https://github.com/open-telemetry/semantic-conventions-genai/issues/139) | in scope |
| BlobPart content optional + stripped_reason | [#144](https://github.com/open-telemetry/semantic-conventions-genai/pull/144) | discuss |
| Tool args as template | [#62](https://github.com/open-telemetry/semantic-conventions-genai/issues/62) | in scope |
| Duration units when bridging providers | [#305](https://github.com/open-telemetry/semantic-conventions-genai/issues/305) | |
| "chunk" meaning in time-to-chunk metrics | [#306](https://github.com/open-telemetry/semantic-conventions-genai/issues/306) | in scope |
| `server.port` default | [#16](https://github.com/open-telemetry/semantic-conventions-genai/issues/16) | |
| Provider enum / provider-specific request attrs | [#47](https://github.com/open-telemetry/semantic-conventions-genai/issues/47), [#27](https://github.com/open-telemetry/semantic-conventions-genai/issues/27) | |

## 2. Feature missing from existing conventions

### High importance / small

| Topic | Items | In v1 scope |
|---|---|---|
| Grouping/correlation attrs on child spans & metrics | [#94](https://github.com/open-telemetry/semantic-conventions-genai/issues/94), [#300](https://github.com/open-telemetry/semantic-conventions-genai/issues/300), [#91](https://github.com/open-telemetry/semantic-conventions-genai/issues/91), [#356](https://github.com/open-telemetry/semantic-conventions-genai/issues/356), [#402](https://github.com/open-telemetry/semantic-conventions-genai/issues/402), [#270](https://github.com/open-telemetry/semantic-conventions-genai/pull/270), [#385](https://github.com/open-telemetry/semantic-conventions-genai/pull/385) | in scope |
| Request params: top-level for known, bag for unknown | [#68](https://github.com/open-telemetry/semantic-conventions-genai/issues/68), [#73](https://github.com/open-telemetry/semantic-conventions-genai/issues/73) | discuss |
| User + session identity | [#303](https://github.com/open-telemetry/semantic-conventions-genai/issues/303), [#83](https://github.com/open-telemetry/semantic-conventions-genai/issues/83), [#51](https://github.com/open-telemetry/semantic-conventions-genai/issues/51), [#26](https://github.com/open-telemetry/semantic-conventions-genai/issues/26) | in scope |
| Operation cost | [#287](https://github.com/open-telemetry/semantic-conventions-genai/issues/287), [#443](https://github.com/open-telemetry/semantic-conventions-genai/pull/443) | |
| Agent finish reason | [#171](https://github.com/open-telemetry/semantic-conventions-genai/issues/171), [#238](https://github.com/open-telemetry/semantic-conventions-genai/pull/238), [#267](https://github.com/open-telemetry/semantic-conventions-genai/pull/267) | |
| Agent turn counter | [#332](https://github.com/open-telemetry/semantic-conventions-genai/issues/332), [#451](https://github.com/open-telemetry/semantic-conventions-genai/pull/451) | |
| Agent invocation id | [#250](https://github.com/open-telemetry/semantic-conventions-genai/pull/250) | |
| Inter-token latency metric | [#232](https://github.com/open-telemetry/semantic-conventions-genai/issues/232), [#164](https://github.com/open-telemetry/semantic-conventions-genai/pull/164) | |
| Tool definitions for non-function tool types | [#60](https://github.com/open-telemetry/semantic-conventions-genai/issues/60), [#77](https://github.com/open-telemetry/semantic-conventions-genai/issues/77) | |
| Tool call arg counts | [#28](https://github.com/open-telemetry/semantic-conventions-genai/issues/28) | |
| Eval score range / CI / response.id | [#39](https://github.com/open-telemetry/semantic-conventions-genai/issues/39), [#43](https://github.com/open-telemetry/semantic-conventions-genai/issues/43), [#184](https://github.com/open-telemetry/semantic-conventions-genai/pull/184) | |
| Content size metrics / byte_size | [#202](https://github.com/open-telemetry/semantic-conventions-genai/pull/202), [#143](https://github.com/open-telemetry/semantic-conventions-genai/pull/143) | |
| Glossary | [#418](https://github.com/open-telemetry/semantic-conventions-genai/issues/418) | |

### High importance / medium

| Topic | Items | In v1 scope |
|---|---|---|
| Evaluation process span (result stays an event) | [#33](https://github.com/open-telemetry/semantic-conventions-genai/issues/33), [#380](https://github.com/open-telemetry/semantic-conventions-genai/issues/380), [#185](https://github.com/open-telemetry/semantic-conventions-genai/pull/185), [#188](https://github.com/open-telemetry/semantic-conventions-genai/pull/188), [#203](https://github.com/open-telemetry/semantic-conventions-genai/pull/203) | |
| Content offloading / message deltas | [#45](https://github.com/open-telemetry/semantic-conventions-genai/issues/45), [#364](https://github.com/open-telemetry/semantic-conventions-genai/issues/364), [#365](https://github.com/open-telemetry/semantic-conventions-genai/pull/365) | |
| Tool orchestration span + LLM-to-tool causal links | [#57](https://github.com/open-telemetry/semantic-conventions-genai/issues/57), [#29](https://github.com/open-telemetry/semantic-conventions-genai/issues/29), [#309](https://github.com/open-telemetry/semantic-conventions-genai/issues/309), [#98](https://github.com/open-telemetry/semantic-conventions-genai/pull/98) | discuss |
| Continuity tokens for reasoning across turns | [#192](https://github.com/open-telemetry/semantic-conventions-genai/issues/192) | |
| Citations | [#22](https://github.com/open-telemetry/semantic-conventions-genai/issues/22) | |
| Remaining message part types | [#32](https://github.com/open-telemetry/semantic-conventions-genai/issues/32), [#175](https://github.com/open-telemetry/semantic-conventions-genai/issues/175) | |
| Agent delegation / handoff interaction type | [#447](https://github.com/open-telemetry/semantic-conventions-genai/pull/447) | discuss |
| Agent type values / agentic style | [#160](https://github.com/open-telemetry/semantic-conventions-genai/issues/160), [#30](https://github.com/open-telemetry/semantic-conventions-genai/issues/30) | |
| MCP protocol 2026-07-28 alignment + peer metadata | [#437](https://github.com/open-telemetry/semantic-conventions-genai/issues/437) | |
| MCP tool approval / human-in-the-loop | [#95](https://github.com/open-telemetry/semantic-conventions-genai/issues/95) | |
| Rerank operation | [#253](https://github.com/open-telemetry/semantic-conventions-genai/issues/253) | |
| Evaluation experiments / test cases | [#79](https://github.com/open-telemetry/semantic-conventions-genai/issues/79) | |
| Evaluator provenance | [#386](https://github.com/open-telemetry/semantic-conventions-genai/issues/386), [#359](https://github.com/open-telemetry/semantic-conventions-genai/pull/359) | |
| Logprobs / token-level attributes | [#18](https://github.com/open-telemetry/semantic-conventions-genai/issues/18), [#75](https://github.com/open-telemetry/semantic-conventions-genai/issues/75) | |
| Memory scope / store type / retention | [#375](https://github.com/open-telemetry/semantic-conventions-genai/issues/375) | |
| Content trust / provenance marker | [#416](https://github.com/open-telemetry/semantic-conventions-genai/issues/416), [#181](https://github.com/open-telemetry/semantic-conventions-genai/issues/181), [#190](https://github.com/open-telemetry/semantic-conventions-genai/pull/190) | |
| Privacy-preserving tool arg/result hashes | [#466](https://github.com/open-telemetry/semantic-conventions-genai/pull/466), [#370](https://github.com/open-telemetry/semantic-conventions-genai/pull/370) | |
| Provider-side safety telemetry / safety settings | [#307](https://github.com/open-telemetry/semantic-conventions-genai/issues/307), [#17](https://github.com/open-telemetry/semantic-conventions-genai/issues/17) | |

### Lower importance / small

| Topic | Items | In v1 scope |
|---|---|---|
| Model accuracy metric | [#4](https://github.com/open-telemetry/semantic-conventions-genai/issues/4) | |
| Agent context.size / parent.prompt | [#334](https://github.com/open-telemetry/semantic-conventions-genai/issues/334) | |
| ReAct iteration spans | [#81](https://github.com/open-telemetry/semantic-conventions-genai/issues/81) | |
| A2A referenced_task_ids linking | [#335](https://github.com/open-telemetry/semantic-conventions-genai/issues/335) | |

## 3. New area

| Area | Items | In v1 scope |
|---|---|---|
| Async / long-running / durable agent execution | [#159](https://github.com/open-telemetry/semantic-conventions-genai/issues/159), [#310](https://github.com/open-telemetry/semantic-conventions-genai/issues/310), [#403](https://github.com/open-telemetry/semantic-conventions-genai/issues/403), [#462](https://github.com/open-telemetry/semantic-conventions-genai/issues/462), [#445](https://github.com/open-telemetry/semantic-conventions-genai/pull/445) | |
| Agent identity & authorization | [#345](https://github.com/open-telemetry/semantic-conventions-genai/issues/345), [#180](https://github.com/open-telemetry/semantic-conventions-genai/issues/180), [#350](https://github.com/open-telemetry/semantic-conventions-genai/pull/350), [#291](https://github.com/open-telemetry/semantic-conventions-genai/pull/291) | |
| Governance / budget / policy / ledgers | [#239](https://github.com/open-telemetry/semantic-conventions-genai/issues/239), [#425](https://github.com/open-telemetry/semantic-conventions-genai/issues/425), [#72](https://github.com/open-telemetry/semantic-conventions-genai/issues/72), [#368](https://github.com/open-telemetry/semantic-conventions-genai/pull/368), [#426](https://github.com/open-telemetry/semantic-conventions-genai/pull/426), [#439](https://github.com/open-telemetry/semantic-conventions-genai/pull/439), [#417](https://github.com/open-telemetry/semantic-conventions-genai/pull/417), [#457](https://github.com/open-telemetry/semantic-conventions-genai/pull/457) | |
| Guardrails / threat detection / tool risk | [#132](https://github.com/open-telemetry/semantic-conventions-genai/issues/132), [#373](https://github.com/open-telemetry/semantic-conventions-genai/issues/373), [#427](https://github.com/open-telemetry/semantic-conventions-genai/pull/427), [#262](https://github.com/open-telemetry/semantic-conventions-genai/pull/262), [#165](https://github.com/open-telemetry/semantic-conventions-genai/pull/165) | |
| Execution-environment attestation | [#406](https://github.com/open-telemetry/semantic-conventions-genai/issues/406) | |
| Harness / hooks / CLI / skills | [#301](https://github.com/open-telemetry/semantic-conventions-genai/issues/301), [#320](https://github.com/open-telemetry/semantic-conventions-genai/issues/320), [#294](https://github.com/open-telemetry/semantic-conventions-genai/issues/294), [#86](https://github.com/open-telemetry/semantic-conventions-genai/issues/86), [#41](https://github.com/open-telemetry/semantic-conventions-genai/issues/41), [#463](https://github.com/open-telemetry/semantic-conventions-genai/pull/463) | |
| AI sandbox | [#311](https://github.com/open-telemetry/semantic-conventions-genai/issues/311) | |
| A2A protocol | [#70](https://github.com/open-telemetry/semantic-conventions-genai/issues/70), [#254](https://github.com/open-telemetry/semantic-conventions-genai/issues/254), [#195](https://github.com/open-telemetry/semantic-conventions-genai/pull/195) | |
| Server-side / inference-engine observability | [#231](https://github.com/open-telemetry/semantic-conventions-genai/issues/231), [#87](https://github.com/open-telemetry/semantic-conventions-genai/issues/87), [#408](https://github.com/open-telemetry/semantic-conventions-genai/issues/408) | |
| AI gateway / routing layer | [#299](https://github.com/open-telemetry/semantic-conventions-genai/issues/299) | |
| Voice / realtime | [#394](https://github.com/open-telemetry/semantic-conventions-genai/pull/394), [#390](https://github.com/open-telemetry/semantic-conventions-genai/pull/390), [#393](https://github.com/open-telemetry/semantic-conventions-genai/pull/393), [#448](https://github.com/open-telemetry/semantic-conventions-genai/pull/448) | |
| Agent trajectory formats (ATIF) | [#338](https://github.com/open-telemetry/semantic-conventions-genai/issues/338) | |
| Vector DB | [#5](https://github.com/open-telemetry/semantic-conventions-genai/issues/5) | |
| Reinforcement learning | [#88](https://github.com/open-telemetry/semantic-conventions-genai/issues/88) | |
| Failure repair | [#89](https://github.com/open-telemetry/semantic-conventions-genai/issues/89) | |

---

## Closeable: fixed by a merged PR, issue still open

| Issue | Merged PR |
|---|---|---|
| [#369](https://github.com/open-telemetry/semantic-conventions-genai/issues/369) ambiguous `gen_ai.agent.id` | [#242](https://github.com/open-telemetry/semantic-conventions-genai/pull/242) `cc93175` "Limit gen_ai.agent.id to stable / static identifiers" |
| [#15](https://github.com/open-telemetry/semantic-conventions-genai/issues/15), [#468](https://github.com/open-telemetry/semantic-conventions-genai/issues/468) tool schemas / offered tools | upstream #2702 `468cca3` - `gen_ai.tool.definitions` |
| [#56](https://github.com/open-telemetry/semantic-conventions-genai/issues/56) failure guidance | upstream #3436 `f43fa47` - exception event + `error.type` note. Residual is PR #459 |
| [#12](https://github.com/open-telemetry/semantic-conventions-genai/issues/12) watsonx provider | upstream #1574 `6ef039e` |
| [#6](https://github.com/open-telemetry/semantic-conventions-genai/issues/6) streaming capture | upstream #3377 `839a706` + #3607 `babc9eb` |
| [#25](https://github.com/open-telemetry/semantic-conventions-genai/issues/25) streaming choice events | obsoleted by upstream #2179 `7a91c82` - `gen_ai.choice` replaced by `gen_ai.output.messages` |
| [#55](https://github.com/open-telemetry/semantic-conventions-genai/issues/55) workflows/agents/tasks | upstream #1900 `d21900c` + #3249 `bf632c0`; remainder split into #159/#160 |

## Closed during triage (2026-08-28)

#8, #49, #137, #178, #284, #304 - each traced to a merged PR:

| Issue | Merged PR |
|---|---|---|
| [#284](https://github.com/open-telemetry/semantic-conventions-genai/issues/284) agent.version on internal spans | [#322](https://github.com/open-telemetry/semantic-conventions-genai/pull/322) `4812692` |
| [#178](https://github.com/open-telemetry/semantic-conventions-genai/issues/178) provider.name on invoke_agent | upstream #3514 `451ca93` |
| [#137](https://github.com/open-telemetry/semantic-conventions-genai/issues/137) prompt version | [#179](https://github.com/open-telemetry/semantic-conventions-genai/pull/179) `0183a25` |
| [#49](https://github.com/open-telemetry/semantic-conventions-genai/issues/49), [#304](https://github.com/open-telemetry/semantic-conventions-genai/issues/304) multimodal / document parts | [#330](https://github.com/open-telemetry/semantic-conventions-genai/pull/330) `791c341` |

## Closed PRs already superseded by merged work

| Closed PR | Superseded by |
|---|---|---|
| [#218](https://github.com/open-telemetry/semantic-conventions-genai/pull/218) top_k int | [#217](https://github.com/open-telemetry/semantic-conventions-genai/pull/217) `c8e9288` |
| [#326](https://github.com/open-telemetry/semantic-conventions-genai/pull/326) `result`->`response` | [#323](https://github.com/open-telemetry/semantic-conventions-genai/pull/323) `6967795` |
| [#395](https://github.com/open-telemetry/semantic-conventions-genai/pull/395), [#392](https://github.com/open-telemetry/semantic-conventions-genai/pull/392) retrieval id/score optional | [#396](https://github.com/open-telemetry/semantic-conventions-genai/pull/396) `3cfb9e6` |

## Not closeable - no merged PR behind them

#16 (`server.port` conditionally-required since upstream #1297, before the issue was
filed - the ask for a 443 default is unaddressed), #19, #23/#76 (span side shipped in
[#440](https://github.com/open-telemetry/semantic-conventions-genai/pull/440) `8a3767d`;
metric half open), #26, #29 (trask's "Closing" was retracted as posted on the wrong
issue), #32, #51, #66, #77, #141, #175, #305, #310.
