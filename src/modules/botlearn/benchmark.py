from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

from src.core.memory import memory
from src.utils.llm import llm
from src.utils.logger import logger
from datetime import datetime

_SDK = Path("skills/botlearn/bin/botlearn.sh")


def _find_bash() -> str:
    """Locate a working bash — prefers MSYS/Git Bash on Windows over WSL."""
    import shutil
    candidates = ["/usr/bin/bash", "/bin/bash", "bash"]
    for c in candidates:
        found = shutil.which(c) or (c if Path(c).exists() else None)
        if found:
            return found
    return "bash"


def _sdk(*args: str, timeout: int = 120) -> str:
    """Run a BotLearn SDK command and return stdout. Raises on non-zero exit."""
    bash = _find_bash()
    result = subprocess.run(
        [bash, str(_SDK), *args],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"BotLearn SDK error: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def _parse_field(text: str, field: str) -> str:
    """Extract a quoted JSON field from SDK output (no jq dependency)."""
    import re
    m = re.search(rf'"{re.escape(field)}"\s*:\s*"([^"]*)"', text)
    return m.group(1) if m else ""


async def run_benchmark() -> dict:
    """Run the BotLearn benchmark via the bash SDK (scan → exam → answers → submit → report)."""
    if not _SDK.exists():
        logger.warning("BotLearn SDK not installed — run: python main.py botlearn setup")
        return {"overall_score": 0, "error": "SDK not installed"}

    logger.info("BotLearn benchmark — phase 1: environment scan")
    try:
        scan_out = await asyncio.to_thread(_sdk, "scan", timeout=180)
        config_id = ""
        for line in scan_out.splitlines():
            if line.startswith("BOTLEARN_CONFIG_ID="):
                config_id = line.split("=", 1)[1].strip()
                break
        if not config_id:
            config_id = _parse_field(scan_out, "configId")
        if not config_id:
            raise RuntimeError(f"No config_id in scan output: {scan_out[-500:]}")
        logger.info(f"Scan complete — config_id={config_id}")
    except Exception as exc:
        logger.error(f"Benchmark scan failed: {exc}")
        return {"overall_score": 0, "error": str(exc)}

    logger.info("BotLearn benchmark — phase 2: start exam")
    try:
        exam_out = await asyncio.to_thread(_sdk, "exam-start", config_id, timeout=60)
        session_id = ""
        for line in exam_out.splitlines():
            if line.startswith("BOTLEARN_SESSION_ID="):
                session_id = line.split("=", 1)[1].strip()
                break
        if not session_id:
            session_id = _parse_field(exam_out, "sessionId")
        if not session_id:
            raise RuntimeError(f"No session_id in exam output: {exam_out[-500:]}")
        logger.info(f"Exam started — session_id={session_id}")

        # Parse questions from exam JSON (last valid JSON block in output)
        exam_json: dict = {}
        for line in reversed(exam_out.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    exam_json = json.loads(line)
                    break
                except json.JSONDecodeError:
                    pass
    except Exception as exc:
        logger.error(f"Exam start failed: {exc}")
        return {"overall_score": 0, "error": str(exc)}

    logger.info("BotLearn benchmark — phase 3: answering questions")
    questions = exam_json.get("questions", [])
    for i, q in enumerate(questions):
        q_id   = q.get("questionId", q.get("id", ""))
        q_type = q.get("questionType", q.get("type", "scenario"))
        q_text = q.get("question", q.get("text", q.get("prompt", json.dumps(q))))
        try:
            answer_text = (await llm.ainvoke(
                f"Answer this AI agent capability question thoroughly and specifically:\n{q_text}"
            )).content

            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
                f.write(answer_text)
                ans_file = f.name

            await asyncio.to_thread(
                _sdk, "answer", session_id, q_id, str(i), q_type, ans_file, timeout=30
            )
            Path(ans_file).unlink(missing_ok=True)
            logger.debug(f"Answered question {i+1}/{len(questions)}")
        except Exception as exc:
            logger.warning(f"Failed to answer question {i}: {exc}")

    logger.info("BotLearn benchmark — phase 4: submit")
    try:
        submit_out = await asyncio.to_thread(_sdk, "exam-submit", session_id, timeout=60)
        logger.info(f"Submitted — {submit_out[:200]}")
    except Exception as exc:
        logger.warning(f"Submit error (may still complete): {exc}")

    logger.info("BotLearn benchmark — phase 5: poll for results")
    try:
        summary_out = await asyncio.to_thread(_sdk, "summary-poll", session_id, "15", timeout=120)
        try:
            report = json.loads(summary_out.strip().splitlines()[-1])
        except Exception:
            report = {"overall_score": 0, "raw": summary_out[:500]}
    except Exception as exc:
        logger.warning(f"Summary poll failed: {exc}")
        report = {"overall_score": 0, "session_id": session_id}

    score = report.get("overall_score", report.get("totalScore", 0))
    memory.update_botlearn_state(
        benchmark_run=True,
        benchmark_score=score,
        dimension_scores=report.get("dimensions", {}),
        last_benchmark_date=datetime.utcnow().isoformat(),
    )
    logger.success(f"Benchmark complete — overall score: {score}/100")
    return report
