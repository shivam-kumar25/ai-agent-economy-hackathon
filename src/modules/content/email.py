from __future__ import annotations

import re


def split_sequence(raw: str) -> list[dict]:
    """Parse a raw LLM email sequence into a list of {subject, body} dicts.

    Expects the LLM to separate emails with '---' and label each block with
    'Subject:' on the first line.
    """
    blocks = re.split(r"\n---+\n", raw.strip())
    emails: list[dict] = []
    for block in blocks:
        lines = block.strip().splitlines()
        subject = ""
        body_lines: list[str] = []
        for i, line in enumerate(lines):
            if line.lower().startswith("subject:"):
                subject = line.split(":", 1)[1].strip()
            else:
                body_lines = lines[i:]
                break
        emails.append({"subject": subject, "body": "\n".join(body_lines).strip()})
    return [e for e in emails if e["subject"] or e["body"]]


def personalize(template: str, variables: dict[str, str]) -> str:
    """Replace {{key}} placeholders in the template."""
    for key, value in variables.items():
        template = template.replace("{{" + key + "}}", value)
    return template
