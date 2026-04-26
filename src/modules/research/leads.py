from __future__ import annotations

import pandas as pd

from src.models.research import LeadList
from src.utils.logger import logger


def export_leads(lead_list: LeadList, base_path: str) -> None:
    """Export lead list to CSV and JSON alongside the markdown output."""
    if not lead_list.leads:
        return
    df = pd.DataFrame([lead.model_dump() for lead in lead_list.leads])
    df = df.sort_values("confidence", ascending=False) if "confidence" in df.columns else df
    df.to_csv(f"{base_path}.csv", index=False)
    df.to_json(f"{base_path}.json", orient="records", indent=2)
    logger.info(f"Leads exported: {base_path}.csv / .json")
