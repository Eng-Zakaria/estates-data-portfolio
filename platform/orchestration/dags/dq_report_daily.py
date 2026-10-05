"""Daily DQ digest: summarise quality results and email them.

P03 hook: until platform/quality lands, the digest reports the P01
reconciliation + quarantine counts and says so explicitly.
"""

from __future__ import annotations

import json

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from common import COMMON_TAGS, DEFAULT_ARGS, MAX_ACTIVE_RUNS, OWNER
from tasks.pipeline import LAKE, REPO, send_alert


def _digest(**context) -> dict:
    quality_store = REPO / "platform" / "quality" / "dq_results.json"
    lines = ["Estates DQ daily digest (synthetic data)."]
    if quality_store.exists():
        payload = json.loads(quality_store.read_text(encoding="utf-8-sig"))
        results = payload.get("results", [])
        failed = [r for r in results if r.get("status") != "pass"]
        lines.append(f"checks={len(results)} failing={len(failed)}")
        for row in failed[:10]:
            lines.append(f"  - {row.get('dataset')}.{row.get('check_id')}: {row.get('status')}")
    else:
        recon_file = LAKE / "reconciliation.json"
        if recon_file.exists():
            report = json.loads(recon_file.read_text(encoding="utf-8"))
            for row in report:
                lines.append(f"  - {row.get('source')}: silver+quarantine reconciled={row.get('pass')}")
        lines.append("NOTE: platform/quality not built yet (P03); full scorecard pending.")
    body = "\n".join(lines)
    mailed = send_alert("DQ daily digest", body)
    return {"mailed": mailed, "lines": len(lines)}


with DAG(
    dag_id="dq_report_daily",
    schedule="@daily",
    catchup=False,
    max_active_runs=MAX_ACTIVE_RUNS,
    default_args=DEFAULT_ARGS,
    tags=COMMON_TAGS + ["dq"],
    owner=OWNER,
    doc_md=__doc__,
) as dag:
    digest = PythonOperator(task_id="dq_digest_email", python_callable=_digest)
