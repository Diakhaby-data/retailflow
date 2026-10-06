"""
Parse transform/target/run_results.json (genere par le dernier appel dbt,
ici 'dbt test') et pousse le compte de tests reussis/echoues. Appelee avec
trigger_rule="all_done" dans le DAG : elle doit tourner meme si dbt_test a
echoue, puisque c'est justement dans ce cas que ce signal compte le plus.
"""
import json
from pathlib import Path

from src.monitoring.metrics import push_dbt_test_metrics

RUN_RESULTS_PATH = Path("transform/target/run_results.json")


def main():
    data = json.loads(RUN_RESULTS_PATH.read_text())
    statuses = [r["status"] for r in data["results"]]

    passed = statuses.count("pass")
    failed = sum(1 for s in statuses if s in ("fail", "error"))

    print(f"Tests dbt : {passed} reussis, {failed} echoues sur {len(statuses)} total")
    push_dbt_test_metrics(passed, failed)


if __name__ == "__main__":
    main()
