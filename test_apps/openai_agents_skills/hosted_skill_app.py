"""Run an OpenAI agent with a dashboard-hosted skill."""

import asyncio
import os

from agents import Agent, ModelSettings, Runner, ShellTool, ShellToolSkillReference
from agents.run import RunConfig


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Set {name} in .env")
    return value


def build_agent() -> Agent[None]:
    skill: ShellToolSkillReference = {
        "type": "skill_reference",
        "skill_id": required_env("OPENAI_SKILL_ID"),
    }
    if version := os.getenv("OPENAI_SKILL_VERSION"):
        skill["version"] = version

    return Agent(
        name="hosted_skill_test_agent",
        model=os.getenv("MODEL", "gpt-5.6-sol"),
        instructions=(
            "Use the configured hosted skill when relevant. Follow its instructions "
            "and run its bundled scripts when requested."
        ),
        tools=[
            ShellTool(
                environment={
                    "type": "container_auto",
                    "skills": [skill],
                }
            )
        ],
        model_settings=ModelSettings(tool_choice="required"),
    )


async def main() -> None:
    prompt = required_env("PROMPT")
    result = await Runner.run(
        build_agent(),
        prompt,
        run_config=RunConfig(workflow_name="openai-agents-hosted-skill-test"),
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
