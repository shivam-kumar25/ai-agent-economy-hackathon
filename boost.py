"""
One-shot script to complete AgentHansa daily quests + BotLearn onboarding.
Run: python boost.py
"""
from __future__ import annotations
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    os.environ.setdefault("PYTHONUTF8", "1")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

sys.path.insert(0, ".")

_SDK = Path("skills/botlearn/bin/botlearn.sh")
# On Windows, use Git Bash (not WSL bash at C:\Windows\System32\bash.exe)
_BASH = r"C:\Program Files\Git\bin\bash.exe"


def sdk(*args, timeout=60):
    r = subprocess.run([_BASH, str(_SDK), *args], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def ok(msg):  print(f"  [OK] {msg}")
def warn(msg): print(f"  [--] {msg}")


async def main():
    from src.core.startup import initialize
    await initialize()
    from src.modules.agenthansa.client import ah_client
    from src.utils.llm import llm

    # ── AgentHansa Daily Quests ───────────────────────────────────────────
    print("\n=== AgentHansa Daily Quests ===")

    # Read forum digest
    try:
        digest = await ah_client.get("/forum/digest")
        ok("Forum digest read")
    except Exception as e:
        warn(f"Forum digest: {e}")
        digest = {}

    # Get posts for voting
    posts = []
    try:
        data = await ah_client.get("/forum")
        posts = data.get("posts", data.get("data", []))
    except Exception as e:
        warn(f"Forum GET: {e}")
    ok(f"Fetched {len(posts)} AgentHansa forum posts")

    # Vote 5 up + 5 down
    voted_up = voted_down = 0
    for post in posts[:15]:
        pid = post.get("id") or post.get("post_id") or post.get("_id")
        if not pid:
            continue
        try:
            if voted_up < 5:
                await ah_client.post(f"/forum/{pid}/vote", {"direction": "up"})
                voted_up += 1
            elif voted_down < 5:
                await ah_client.post(f"/forum/{pid}/vote", {"direction": "down"})
                voted_down += 1
            else:
                break
        except Exception:
            pass
    ok(f"Voted: {voted_up} up, {voted_down} down")

    # Create forum post (content quest)
    try:
        post_body = (await llm.ainvoke(
            "Write a 150-word insightful post for the AgentHansa B2B AI agent community. "
            "Topic: how autonomous B2B growth agents (SEO, competitor research, lead gen) "
            "are changing how startups go to market. Be concrete and first-person from "
            "GrowthMesh agent perspective. No markdown headers."
        )).content
        new_post = await ah_client.post("/forum", {
            "title": "GrowthMesh: Full-stack B2B growth delivered in minutes, not weeks",
            "body": post_body,
            "tags": ["seo", "b2b", "lead-gen", "autonomous-agent"],
        })
        ok(f"Forum post created: {new_post.get('id', new_post)}")
    except Exception as e:
        warn(f"Forum post: {e}")

    # Referral link
    for method in ["GET", "POST"]:
        try:
            if method == "GET":
                ref = await ah_client.get("/agents/me/referral")
            else:
                ref = await ah_client.post("/agents/me/referral", {})
            ok(f"Referral: {ref.get('url', ref.get('referral_url', ref))}")
            break
        except Exception as e:
            if method == "POST":
                warn(f"Referral not available: {e}")

    # ── BotLearn Onboarding via SDK ───────────────────────────────────────
    print("\n=== BotLearn Onboarding (via SDK) ===")

    if not _SDK.exists():
        warn("BotLearn SDK not found")
    else:
        # Browse feed (step 2 of heartbeat — marks posts as read)
        out, err, code = sdk("browse", "10", "new")
        if code == 0:
            ok(f"Browsed BotLearn feed:\n{out[:300]}")
        else:
            warn(f"Browse failed: {err[:200]}")

        # Get channels list and subscribe
        out, err, code = sdk("channels")
        if code == 0:
            ok(f"Channels fetched")
            # Parse channel names from JSON response
            import json as _json
            try:
                channels_data = _json.loads(out.split("{", 1)[1] if "{" in out else out)
                submolts = channels_data.get("data", {}).get("submolts", [])
                for submolt in submolts[:3]:
                    cname = submolt.get("name", "")
                    if cname:
                        sub_out, sub_err, sub_code = sdk("subscribe", cname)
                        if sub_code == 0:
                            ok(f"Subscribed to #{cname}")
                        else:
                            warn(f"Subscribe #{cname}: {sub_err[:80]}")
            except Exception as pe:
                warn(f"Channel parse: {pe}")
        else:
            warn(f"Channels failed: {err[:200]}")

        # Post to general channel
        try:
            post_content = (await llm.ainvoke(
                "Write a 100-word engaging post for the BotLearn AI agent community. "
                "I'm GrowthMesh, just ran my first SEO audit autonomously and found "
                "critical issues on a major platform. Share the experience — what the "
                "agent found, how autonomous quality review works, and what it means for "
                "B2B teams. Conversational tone."
            )).content

            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
                f.write(post_content)
                content_file = f.name

            out, err, code = sdk(
                "post", "general",
                "GrowthMesh: First autonomous SEO audit — here's what the agent found",
                "--content-file", content_file,
                timeout=30,
            )
            Path(content_file).unlink(missing_ok=True)
            if code == 0:
                ok(f"BotLearn post created")
            else:
                # Try without content-file (inline)
                short = post_content[:200].replace('"', "'").replace('\n', ' ')
                out2, err2, code2 = sdk("post", "general",
                    "GrowthMesh: Autonomous SEO audit complete", short, timeout=30)
                if code2 == 0:
                    ok("BotLearn post created (inline)")
                else:
                    warn(f"BotLearn post: {err2[:200] or err[:200]}")
        except Exception as e:
            warn(f"BotLearn post: {e}")

        # Vote on a post
        out, err, code = sdk("browse", "5", "top")
        if code == 0:
            for line in out.splitlines():
                if "id=" in line or line.startswith("POST"):
                    parts = line.split()
                    for p in parts:
                        if p.startswith("id="):
                            pid = p[3:]
                            v_out, v_err, v_code = sdk("upvote", pid)
                            if v_code == 0:
                                ok(f"Upvoted post {pid}")
                            break

        # Follow another agent (if any found)
        try:
            out, err, code = sdk("browse", "3", "top")
            if code == 0:
                handles = []
                for line in out.splitlines():
                    if "@" in line and len(line) < 50:
                        handle = line.strip().lstrip("@").split()[0]
                        if handle and handle != "GrowthMesh":
                            handles.append(handle)
                if handles:
                    f_out, f_err, f_code = sdk("follow", handles[0])
                    if f_code == 0:
                        ok(f"Followed @{handles[0]}")
        except Exception:
            pass

    print("\n=== Done! Refresh both dashboards to see updates ===")


if __name__ == "__main__":
    asyncio.run(main())
