"""
Metriques custom du pipeline, poussees vers un Pushgateway Prometheus.
Un Pushgateway existe parce que Prometheus fonctionne en modele "pull"
(il va chercher les metriques sur un endpoint HTTP permanent), alors que
les taches Airflow sont des process batch qui demarrent puis s'arretent :
elles n'ont rien a scraper. Le Pushgateway sert d'intermediaire permanent
que ces taches alimentent, et que Prometheus scrape comme un service normal.

On utilise pushadd_to_gateway (POST) et non push_to_gateway (PUT) : PUT
remplace TOUT le contenu du groupe designe par grouping_key, pas seulement
la metrique poussee. Comme plusieurs metriques differentes partagent la
meme grouping_key={"table": ...} ici (lignes ingerees, puis qualite), PUT
effacerait la precedente a chaque nouvel appel. POST ne remplace que les
metriques du meme nom au sein du groupe, laissant les autres intactes.
"""
import os

from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway

PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "http://pushgateway:9091")
JOB_NAME = "retailflow_pipeline"


def push_ingestion_metric(table: str, rows: int) -> None:
    registry = CollectorRegistry()
    gauge = Gauge(
        "retailflow_rows_ingested",
        "Nombre de lignes ingerees lors du dernier run, par table",
        registry=registry,
    )
    gauge.set(rows)
    pushadd_to_gateway(PUSHGATEWAY_URL, job=JOB_NAME, registry=registry, grouping_key={"table": table})


def push_quality_metric(table: str, pass_rate: float) -> None:
    registry = CollectorRegistry()
    gauge = Gauge(
        "retailflow_data_quality_pass_rate",
        "Pourcentage de lignes validees lors du dernier run, par table (0 a 100)",
        registry=registry,
    )
    gauge.set(pass_rate)
    pushadd_to_gateway(PUSHGATEWAY_URL, job=JOB_NAME, registry=registry, grouping_key={"table": table})


def push_dbt_test_metrics(passed: int, failed: int) -> None:
    registry = CollectorRegistry()
    passed_gauge = Gauge("retailflow_dbt_tests_passed", "Tests dbt reussis au dernier run", registry=registry)
    failed_gauge = Gauge("retailflow_dbt_tests_failed", "Tests dbt echoues au dernier run", registry=registry)
    passed_gauge.set(passed)
    failed_gauge.set(failed)
    pushadd_to_gateway(PUSHGATEWAY_URL, job=JOB_NAME, registry=registry, grouping_key={"stage": "dbt_test"})


def push_pipeline_success() -> None:
    registry = CollectorRegistry()
    gauge = Gauge(
        "retailflow_last_success_timestamp",
        "Timestamp Unix du dernier run du pipeline arrive jusqu'a dbt test",
        registry=registry,
    )
    gauge.set_to_current_time()
    pushadd_to_gateway(PUSHGATEWAY_URL, job=JOB_NAME, registry=registry, grouping_key={"stage": "final"})
