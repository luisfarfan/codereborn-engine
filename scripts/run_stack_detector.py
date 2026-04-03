"""
CodeReborn — StackDetector Verification & Demo.

This script runs the deterministic StackDetector agent against any repository path,
persists the findings in PostgreSQL, and displays a summary of the technology DNA.

Usage:
    python scripts/run_stack_detector.py --path /path/to/repo [--json]
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

from sqlmodel import select
from app.infrastructure.database import AsyncSessionFactory, create_db_tables
from app.models.db_models import Job, StackReport
from app.domain.enums import AnalysisDepth, AnalysisMode
from app.agents.stack_detector.agent import StackDetectorAgent

BANNER = r"""
   ______          __     ____ZW____
  / ____/___  ____/ /__  / __ \/ __ \____  _________
 / /   / __ \/ __  / _ \/ /_/ / /_/ / __ \/ ___/ __ \
/ /___/ /_/ / /_/ /  __/ _, _/ _, _/ /_/ / /  / / / /
\____/\____/\__,_/\___/_/ |_/_/ |_/\____/_/  /_/ /_/

          S T A C K   D E T E C T O R
"""


def print_banner():
    print("\033[96m" + BANNER + "\033[0m")
    print("\033[94m" + "─" * 60 + "\033[0m")


def format_table(header, rows):
    print(f"\n\033[93m{header}\033[0m")
    print("─" * 40)
    for k, v in rows:
        print(f"\033[97m{k:<20}\033[0m : {v}")


async def run_verification(repo_path: str, as_json: bool = False):
    if not as_json:
        print_banner()
        print(f"[*] Target: {repo_path}")

    # 1. Ensure tables exist
    await create_db_tables()

    async with AsyncSessionFactory() as session:
        # 2. Create a dummy Job
        job = Job(
            repo_url=None,
            repo_path=str(Path(repo_path).absolute()),
            analysis_depth=AnalysisDepth.QUICK,
            analysis_mode=AnalysisMode.BALANCED,
            status="pending"
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        if not as_json:
            print(f"[*] Created Job ID: {job.id}")
            print("[*] Executing Agent (deterministic)...")

        # 3. Instantiate and execute the Agent
        agent = StackDetectorAgent(session)

        try:
            report_model = await agent.execute(job.id, str(Path(repo_path).absolute()))
            data = report_model.report_data

            if as_json:
                print(json.dumps(data, indent=2))
                return

            print("\n\033[92m✔ Detection Successful!\033[0m")

            # --- Results Summary ---
            summary_info = [
                ("Project Name", data.get("project_name", "Unknown")),
                ("Primary Language", report_model.primary_language),
                ("Analysis Scope", report_model.analysis_scope),
                ("Confidence", f"{report_model.confidence_score * 100:.1f}%"),
            ]
            format_table("Core Identity", summary_info)

            # Languages
            lang_items = data.get("languages", [])
            langs = [f"{li['language']} ({li['estimated_percentage']}%)" for li in lang_items]
            format_table("Languages Distribution", [("Detected", ", ".join(langs))])

            # Frameworks (High-level)
            f_list = data.get('frameworks', [])
            fworks = [f['name'] for f in f_list if "framework" in f.get('category', '')]
            format_table(
                "Frameworks (High-level)",
                [("Identified", ", ".join(fworks) if fworks else "None detected")]
            )

            # Libraries & Tools
            libs = [f['name'] for f in f_list if "framework" not in f.get('category', '')]
            format_table(
                "Libraries & Tools",
                [("Identified", ", ".join(libs) if libs else "None detected")]
            )

            # Services
            services_list = [s['name'] for s in data.get('services', [])]
            format_table(
                "Services",
                [("Identified", ", ".join(services_list) if services_list else "None detected")]
            )

            # Unknown Signals (For 100% Visibility)
            unknown_list = [u['signal'] for u in data.get('unknowns', [])]
            if unknown_list:
                # Group/Limit for readability
                display_unknowns = ", ".join(unknown_list[:15])
                if len(unknown_list) > 15:
                    display_unknowns += f" (+{len(unknown_list) - 15} more)"
                format_table("Other Detected Signals (Unknown)", [("Identified", display_unknowns)])

            # 4. Verify DB persistence independently
            q = select(StackReport).where(StackReport.job_id == job.id)
            verified_res = await session.execute(q)
            verified = verified_res.scalars().first()
            if verified:
                print(f"\n\033[94m[OK] Findings persisted in Database ({job.id})\033[0m")
            else:
                print("\n\033[91m[ERROR] Report not found in database!\033[0m")

        except Exception as e:
            if as_json:
                print(json.dumps({"error": str(e)}))
            else:
                print(f"\n\033[91m[ERROR] Agent execution failed: {str(e)}\033[0m")
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=".", help="Path to the repository to analyze")
    parser.add_argument("--json", action="store_true", help="Output only raw JSON")
    args = parser.parse_args()

    asyncio.run(run_verification(args.path, args.json))
