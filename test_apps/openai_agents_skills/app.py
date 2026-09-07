"""Run an OpenAI sandbox agent with a selectable local skill source."""

import asyncio
import os
from pathlib import Path

from agents import ModelSettings, Runner
from agents.run import RunConfig
from agents.sandbox import SandboxAgent, SandboxRunConfig
from agents.sandbox.capabilities import (
    Capabilities,
    LocalDirLazySkillSource,
    Skill,
    Skills,
)
from agents.sandbox.entries import GitRepo, LocalDir, LocalFile
from agents.sandbox.manifest import Manifest
from agents.sandbox.sandboxes.unix_local import UnixLocalSandboxClient


APP_DIR = Path(__file__).resolve().parent
SKILLS_DIR = APP_DIR / "skills"
SKILL_DIR = SKILLS_DIR / "arithmetic-report"


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Set {name} in .env")
    return value


def build_skills(source: str) -> Skills:
    if source == "lazy":
        return Skills(
            lazy_from=LocalDirLazySkillSource(
                source=LocalDir(src=SKILLS_DIR),
            )
        )
    if source == "eager-dir":
        return Skills(from_=LocalDir(src=SKILLS_DIR))
    if source == "inline":
        return Skills(
            skills=[
                Skill(
                    name="arithmetic-report",
                    description=(
                        "Add two integers with a bundled deterministic script and "
                        "report its output."
                    ),
                    content=(SKILL_DIR / "SKILL.md").read_text(),
                    scripts={
                        "add.py": LocalFile(src=SKILL_DIR / "scripts" / "add.py"),
                        "interactive_add.py": LocalFile(
                            src=SKILL_DIR / "scripts" / "interactive_add.py"
                        ),
                    },
                )
            ]
        )
    if source == "git":
        return Skills(
            from_=GitRepo(
                repo=required_env("SKILL_GIT_REPO"),
                ref=os.getenv("SKILL_GIT_REF", "main"),
                subpath=os.getenv("SKILL_GIT_SUBPATH"),
            )
        )
    raise SystemExit("SKILL_SOURCE must be lazy, eager-dir, inline, or git")


def build_agent() -> SandboxAgent[None]:
    source = os.getenv("SKILL_SOURCE", "lazy")
    skill_usage = (
        "Call load_skill first, then read its SKILL.md and run its bundled script."
        if source == "lazy"
        else "Read the mounted skill's SKILL.md and run its bundled script."
    )
    return SandboxAgent(
        name=f"skill_test_agent_{source.replace('-', '_')}",
        model=os.getenv("MODEL", "gpt-5.6-sol"),
        default_manifest=Manifest(),
        instructions=(
            "Use the $arithmetic-report skill whenever arithmetic is requested. "
            f"{skill_usage} Do not calculate mentally."
        ),
        capabilities=Capabilities.default() + [build_skills(source)],
        model_settings=ModelSettings(tool_choice="required"),
    )


async def main() -> None:
    scenario = os.getenv("SCENARIO", "script")
    prompts = {
        "script": (
            "Use the $arithmetic-report skill to add 37 and 5. Run its script "
            "and report the exact stdout."
        ),
        "reload": (
            "Call load_skill for arithmetic-report twice, then report both exact "
            "tool results."
        ),
        "interactive": (
            "Use arithmetic-report's interactive_add.py to add 37 and 5. Start it "
            "with exec_command using tty=true and yield_time_ms=250. When it returns "
            "a process session ID, send `37\\n5\\n` with write_stdin. Report exact stdout."
        ),
    }
    if scenario not in prompts:
        raise SystemExit("SCENARIO must be script, reload, or interactive")
    prompt = os.getenv("PROMPT", prompts[scenario])
    result = await Runner.run(
        build_agent(),
        prompt,
        run_config=RunConfig(
            workflow_name=(
                "openai-agents-skills-test-"
                f"{os.getenv('SKILL_SOURCE', 'lazy')}-{scenario}"
            ),
            sandbox=SandboxRunConfig(client=UnixLocalSandboxClient()),
        ),
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
