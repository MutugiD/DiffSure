"""Generate and grade public task patches through an authenticated Codex CLI session."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


def run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    timeout: int = 900,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def initialize_repository(source: Path, workspace: Path) -> None:
    shutil.copytree(source, workspace)
    env = os.environ.copy()
    env.update(
        GIT_AUTHOR_NAME="task",
        GIT_AUTHOR_EMAIL="task@example.com",
        GIT_COMMITTER_NAME="task",
        GIT_COMMITTER_EMAIL="task@example.com",
    )
    for command in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "add", "-A"],
        ["git", "commit", "-q", "-m", "snapshot"],
    ):
        completed = run(command, cwd=workspace, env=env)
        if completed.returncode:
            raise RuntimeError(completed.stderr[-1000:])


def generate(
    task_dir: Path,
    task_output: Path,
    codex: str,
    model: str,
    parent_diff: Path | None,
    failure_text: str | None,
) -> tuple[Path, int, float]:
    metadata: dict[str, Any] = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    workspace = task_output / "workspace"
    initialize_repository(task_dir / "repo", workspace)
    if parent_diff is not None:
        applied = run(["git", "apply", str(parent_diff.resolve())], cwd=workspace)
        if applied.returncode:
            raise RuntimeError(applied.stderr[-1000:])

    prompt = (
        "Solve the task below in the current repository. Inspect only files in this repository. "
        "Do not use the network or files outside this repository. You may run the repository's "
        "existing tests. Make the smallest correct source change and leave the completed edits in "
        "the working tree. Do not add explanation or artifacts to the repository.\n\n"
        f"TASK:\n{metadata['task']}\n"
    )
    if failure_text:
        prompt += (
            "\nThis is a bounded repair of the current patch. An independent acceptance gate "
            "observed the failure below. Fix its root cause without changing tests:\n"
            f"{failure_text}\n"
        )

    environment = os.environ.copy()
    environment.pop("OPENAI_API_KEY", None)
    environment.pop("CODEX_API_KEY", None)
    last_message = task_output / "last_message.txt"
    started = time.monotonic()
    completed = run(
        [
            codex,
            "exec",
            "--model",
            model,
            "--sandbox",
            "workspace-write",
            "--skip-git-repo-check",
            "--ignore-rules",
            "--ephemeral",
            "--output-last-message",
            str(last_message),
            "-",
        ],
        cwd=workspace,
        env=environment,
        input_text=prompt,
        timeout=max(600, int(metadata["deadline_seconds"]) + 120),
    )
    elapsed = time.monotonic() - started
    (task_output / "codex.stdout.log").write_text(completed.stdout, encoding="utf-8")
    (task_output / "codex.stderr.log").write_text(completed.stderr, encoding="utf-8")
    diff = run(
        ["git", "-c", "core.autocrlf=false", "diff", "--no-ext-diff", "--no-color"],
        cwd=workspace,
    ).stdout.replace("\r\n", "\n")
    diff_path = task_output / "candidate.diff"
    diff_path.write_text(diff, encoding="utf-8", newline="\n")
    return diff_path, completed.returncode, elapsed


def grade(task_dir: Path, diff_path: Path, image: str) -> dict[str, Any]:
    candidate_root = task_dir.parents[2]
    completed = run(
        [
            "python",
            str(candidate_root / "harness" / "grade.py"),
            "--task",
            str(task_dir),
            "--diff",
            str(diff_path),
            "--image",
            image,
        ],
        cwd=candidate_root,
        timeout=360,
    )
    try:
        result: dict[str, Any] = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result = {
            "verdict": "error",
            "stage": "harness",
            "reason": (completed.stdout + completed.stderr)[-1000:],
        }
    return result


def validate_task(
    task_dir: Path,
    output: Path,
    codex: str,
    model: str,
    image: str,
    parent_diff: Path | None,
    failure_text: str | None,
) -> dict[str, Any]:
    task_output = output / task_dir.name
    task_output.mkdir(parents=True, exist_ok=False)
    diff_path, exit_code, generation_seconds = generate(
        task_dir, task_output, codex, model, parent_diff, failure_text
    )
    result = grade(task_dir, diff_path, image)
    return {
        "task": task_dir.name,
        "model": model,
        "generation_exit_code": exit_code,
        "generation_seconds": round(generation_seconds, 2),
        "diff_bytes": diff_path.stat().st_size,
        "verdict": result.get("verdict"),
        "stage": result.get("stage"),
        "grade_seconds": result.get("duration_s"),
        "reason": result.get("reason"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--image", default="acceptance:latest")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--task", action="append", dest="selected_tasks")
    parser.add_argument("--repair-from", type=Path)
    parser.add_argument("--failure-file", type=Path)
    arguments = parser.parse_args()

    codex = shutil.which("codex.cmd") or shutil.which("codex")
    if codex is None:
        raise SystemExit("codex CLI not found")
    if arguments.output.exists():
        raise SystemExit("output directory already exists; use a fresh evidence directory")
    arguments.output.mkdir(parents=True)

    tasks = sorted((arguments.candidate_root / "tasks" / "public").iterdir())
    if arguments.selected_tasks:
        selected = set(arguments.selected_tasks)
        tasks = [task for task in tasks if task.name in selected]
        missing = selected.difference(task.name for task in tasks)
        if missing:
            raise SystemExit(f"unknown tasks: {', '.join(sorted(missing))}")
    if arguments.repair_from is not None and len(tasks) != 1:
        raise SystemExit("repair mode requires exactly one selected task")
    failure_text = (
        arguments.failure_file.read_text(encoding="utf-8") if arguments.failure_file else None
    )

    with ThreadPoolExecutor(max_workers=arguments.concurrency) as pool:
        rows = list(
            pool.map(
                lambda task: validate_task(
                    task,
                    arguments.output,
                    codex,
                    arguments.model,
                    arguments.image,
                    arguments.repair_from,
                    failure_text,
                ),
                tasks,
            )
        )
    accepted = sum(row["verdict"] == "accept" for row in rows)
    report = {
        "model": arguments.model,
        "mode": "paid_openai_model_benchmark_via_codex_subscription",
        "concurrency": arguments.concurrency,
        "summary": {
            "total": len(rows),
            "accepted": accepted,
            "rejected": len(rows) - accepted,
            "acceptance_rate": accepted / len(rows),
        },
        "tasks": rows,
    }
    (arguments.output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if accepted == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
