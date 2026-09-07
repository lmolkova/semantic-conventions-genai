"""Run an OpenAI native shell tool with local skill execution."""

import asyncio
import os
from pathlib import Path

from agents import (
    Agent,
    ModelSettings,
    Runner,
    ShellCallOutcome,
    ShellCommandOutput,
    ShellCommandRequest,
    ShellResult,
    ShellTool,
)
from agents.run import RunConfig


APP_DIR = Path(__file__).resolve().parent
SKILL_DIR = APP_DIR / "skills" / "arithmetic-report"


async def execute_shell(request: ShellCommandRequest) -> ShellResult:
    outputs: list[ShellCommandOutput] = []
    timeout = (
        request.data.action.timeout_ms / 1000
        if request.data.action.timeout_ms is not None
        else None
    )

    for command in request.data.action.commands:
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=APP_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
            outcome = ShellCallOutcome(type="exit", exit_code=process.returncode)
        except TimeoutError:
            process.kill()
            stdout, stderr = await process.communicate()
            outcome = ShellCallOutcome(type="timeout")

        outputs.append(
            ShellCommandOutput(
                command=command,
                stdout=stdout.decode(errors="replace"),
                stderr=stderr.decode(errors="replace"),
                outcome=outcome,
                provider_data={"tool_call_id": request.data.call_id},
            )
        )

    return ShellResult(
        output=outputs,
        max_output_length=request.data.action.max_output_length,
    )


def build_agent() -> Agent[None]:
    return Agent(
        name="local_shell_skill_test_agent",
        model=os.getenv("MODEL", "gpt-5.6-sol"),
        instructions=(
            "Use the arithmetic-report skill for arithmetic. Read its SKILL.md "
            "and run its bundled script."
        ),
        tools=[
            ShellTool(
                executor=execute_shell,
                environment={
                    "type": "local",
                    "skills": [
                        {
                            "name": "arithmetic-report",
                            "description": (
                                "Add two integers with a bundled deterministic script "
                                "and report its output."
                            ),
                            "path": str(SKILL_DIR),
                        }
                    ],
                },
            )
        ],
        model_settings=ModelSettings(tool_choice="required"),
    )


async def main() -> None:
    prompt = os.getenv(
        "PROMPT",
        "Use arithmetic-report to add 37 and 5. Run its script and report exact stdout.",
    )
    result = await Runner.run(
        build_agent(),
        prompt,
        run_config=RunConfig(workflow_name="openai-agents-local-shell-skill-test"),
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
