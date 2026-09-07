"""Run a Google ADK agent that loads and executes a local skill."""

import asyncio
import os
from pathlib import Path

from google.adk.agents import Agent
from google.adk.code_executors.unsafe_local_code_executor import (
    UnsafeLocalCodeExecutor,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset
from google.genai import types


APP_DIR = Path(__file__).resolve().parent
SKILL_DIR = APP_DIR / "skills" / "arithmetic-report"


async def main() -> None:
    skill = load_skill_from_dir(SKILL_DIR)
    agent = Agent(
        name="skill_test_agent",
        model=os.getenv("MODEL", "gemini-3.6-flash"),
        instruction=(
            "Use the arithmetic-report skill whenever arithmetic is requested. "
            "Load its instructions and run its bundled script instead of calculating mentally."
        ),
        tools=[
            SkillToolset(
                skills=[skill],
                code_executor=UnsafeLocalCodeExecutor(),
            )
        ],
    )

    sessions = InMemorySessionService()
    runner = Runner(agent=agent, app_name="adk_skills_test", session_service=sessions)
    session = await sessions.create_session(
        app_name="adk_skills_test",
        user_id="test-user",
    )
    prompt = os.getenv(
        "PROMPT",
        "Use the arithmetic-report skill to add 37 and 5. Run its script and report the exact stdout.",
    )

    final_text = ""
    async for event in runner.run_async(
        user_id="test-user",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=prompt)],
        ),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(part.text or "" for part in event.content.parts)

    print(final_text)


if __name__ == "__main__":
    asyncio.run(main())
