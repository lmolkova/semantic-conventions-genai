"""Run separate ADK requests covering local skill tool-call variations."""

import asyncio
import os
from pathlib import Path

from google.adk.agents import Agent
from google.adk.code_executors.unsafe_local_code_executor import (
    UnsafeLocalCodeExecutor,
)
from google.adk.environment import LocalEnvironment
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.skills import SkillRegistry, load_skill_from_dir
from google.adk.skills.models import Frontmatter, Skill
from google.adk.tools.skill_toolset import SkillToolset
from google.genai import types


APP_DIR = Path(__file__).resolve().parent
SKILL_DIR = APP_DIR / "skills" / "arithmetic-report"
MODEL = os.getenv("MODEL", "gemini-3.6-flash")


def format_sum(total: int) -> dict[str, int | str]:
    return {"total": total, "formatted": f"The deterministic total is {total}."}


class InMemorySkillRegistry(SkillRegistry):
    def __init__(self, skill: Skill):
        self.skill = skill

    async def get_skill(self, *, name: str) -> Skill:
        if name != self.skill.name:
            raise KeyError(name)
        return self.skill

    async def search_skills(self, *, query: str) -> list[Frontmatter]:
        words = f"{self.skill.name} {self.skill.description}".lower()
        return [self.skill.frontmatter] if query.lower() in words else []


SCENARIOS: dict[str, str] = {
    "catalog": "Call list_skills exactly once and report the returned skill names.",
    "load": "Call load_skill for arithmetic-report, then summarize its instructions.",
    "reload": (
        "Call load_skill for arithmetic-report twice and report both exact tool results."
    ),
    "reference": (
        "Load arithmetic-report, then call load_skill_resource for "
        "references/output-format.md and return its exact content."
    ),
    "asset": (
        "Load arithmetic-report, then call load_skill_resource for "
        "assets/report-template.txt and return its exact content."
    ),
    "script-code-executor": (
        "Load arithmetic-report, then run scripts/add.py with positional arguments "
        "37 and 5. Return exact stdout."
    ),
    "additional-tool": (
        "Load arithmetic-report, then call the format_sum tool exposed by that skill "
        "with total 42. Return its result."
    ),
    "script-environment": (
        "Load arithmetic-report, then run its scripts/add.py in the environment with "
        "the command `python skills/arithmetic-report/scripts/add.py 37 5`. "
        "Return exact stdout."
    ),
    "registry": (
        "Call search_skills with query arithmetic, load the arithmetic-report result, "
        "then run scripts/add.py with positional arguments 37 and 5. Return exact stdout."
    ),
    "missing-resource": (
        "Load arithmetic-report, then call load_skill_resource for "
        "references/missing.md. Report the error without retrying."
    ),
    "missing-script": (
        "Load arithmetic-report, then call run_skill_script for scripts/missing.py. "
        "Report the error without retrying."
    ),
}


def build_toolset(scenario: str, skill: Skill) -> SkillToolset:
    if scenario == "script-environment":
        return SkillToolset(
            skills=[skill],
            environment=LocalEnvironment(),
        )
    if scenario == "registry":
        return SkillToolset(
            registry=InMemorySkillRegistry(skill),
            code_executor=UnsafeLocalCodeExecutor(),
        )
    return SkillToolset(
        skills=[skill],
        code_executor=UnsafeLocalCodeExecutor(),
        additional_tools=[format_sum],
    )


async def run_scenario(name: str, prompt: str) -> None:
    skill = load_skill_from_dir(SKILL_DIR)
    agent = Agent(
        name=f"skill_test_agent_{name.replace('-', '_')}",
        model=MODEL,
        instruction="Follow the requested skill-tool sequence exactly.",
        tools=[build_toolset(name, skill)],
    )
    sessions = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=f"adk_skills_{name}",
        session_service=sessions,
    )
    session = await sessions.create_session(
        app_name=f"adk_skills_{name}",
        user_id="test-user",
    )

    final_text = ""
    try:
        async for event in runner.run_async(
            user_id="test-user",
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(part.text or "" for part in event.content.parts)
    finally:
        await runner.close()

    print(f"[{name}] {final_text}")


async def main() -> None:
    requested = os.getenv("SCENARIOS", "all")
    names = list(SCENARIOS) if requested == "all" else requested.split(",")
    unknown = [name for name in names if name not in SCENARIOS]
    if unknown:
        raise SystemExit(f"Unknown scenarios: {', '.join(unknown)}")

    for name in names:
        try:
            await run_scenario(name, SCENARIOS[name])
        except Exception as error:
            print(f"[{name}] ERROR: {type(error).__name__}: {error}")


if __name__ == "__main__":
    asyncio.run(main())
