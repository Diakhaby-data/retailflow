"""
DAG combine RetailFlow : ingestion multi-sources, data quality, warehouse, dbt.
Ce fichier est lu par le dag-processor d'Airflow, qui tourne dans airflow_venv :
il ne doit donc importer que des modules disponibles dans airflow_venv (Airflow
lui-meme), jamais pandas/sqlalchemy/dbt. Ces dependances-la ne sont necessaires
qu'a l'interieur des sous-process bash lances par BashOperator, qui activent
explicitement le venv principal avant d'appeler python.
"""
from __future__ import annotations

import pendulum
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT_DIR = "/home/dkb/ecommerce"

# Prefixe reutilise par toutes les taches Python : active le bon venv, se place
# a la racine du projet, et stoppe immediatement le script bash au premier
# echec (set -e) plutot que de continuer avec un environnement bancal.
VENV_ACTIVATE = (
    "set -euo pipefail\n"
    f"source {PROJECT_DIR}/venv/bin/activate\n"
    f"cd {PROJECT_DIR}\n"
)

# Pour dbt : meme venv, mais dossier transform/ et variables Postgres du .env.
DBT_ENV = VENV_ACTIVATE + (
    "cd transform\n"
    f"export DBT_PROFILES_DIR={PROJECT_DIR}/transform\n"
    "set -a\nsource ../.env\nset +a\n"
)

default_args = {
    "owner": "diakhaby",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="retailflow_pipeline",
    description="Pipeline quotidien RetailFlow : ingestion, data quality, warehouse, dbt.",
    default_args=default_args,
    schedule="@daily",
    start_date=pendulum.datetime(2026, 9, 13, tz="Europe/Paris"),
    catchup=False,
    tags=["retailflow"],
) as dag:

    check_sources = BashOperator(
        task_id="check_sources",
        bash_command=VENV_ACTIVATE + """
set -a; source .env; set +a

echo "Verification API produits (mock)..."
curl -sf "$MOCK_API_URL/health" > /dev/null

echo "Verification Postgres source..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;" > /dev/null

echo "Verification des fichiers sources..."
test -f data/external/customers.csv
test -f data/external/returns.csv
test -f data/external/inventory.csv
test -f data/external/events.jsonl

echo "Toutes les sources sont disponibles."
""",
    )

    ingest_source_a = BashOperator(
        task_id="ingest_source_a_postgres",
        bash_command=VENV_ACTIVATE + "python scripts/ingest_postgres_source.py",
    )
    ingest_source_b = BashOperator(
        task_id="ingest_source_b_api",
        bash_command=VENV_ACTIVATE + "python scripts/ingest_api_source.py",
    )
    ingest_source_c = BashOperator(
        task_id="ingest_source_c_csv",
        bash_command=VENV_ACTIVATE + "python scripts/ingest_csv_source.py",
    )
    ingest_source_d = BashOperator(
        task_id="ingest_source_d_events",
        bash_command=VENV_ACTIVATE + "python scripts/ingest_events_source.py",
    )

    validate_simple = BashOperator(
        task_id="validate_simple",
        bash_command=VENV_ACTIVATE + "python scripts/validate_simple.py",
    )
    validate_orders = BashOperator(
        task_id="validate_orders",
        bash_command=VENV_ACTIVATE + "python scripts/validate_orders.py",
    )
    validate_order_items = BashOperator(
        task_id="validate_order_items",
        bash_command=VENV_ACTIVATE + "python scripts/validate_order_items.py",
    )
    validate_payments = BashOperator(
        task_id="validate_payments",
        bash_command=VENV_ACTIVATE + "python scripts/validate_payments.py",
    )

    build_dim_date = BashOperator(
        task_id="build_dim_date",
        bash_command=VENV_ACTIVATE + "python scripts/build_dim_date.py",
    )
    load_dimensions = BashOperator(
        task_id="load_dimensions",
        bash_command=VENV_ACTIVATE + "python scripts/load_dimensions.py",
    )
    load_facts = BashOperator(
        task_id="load_facts",
        bash_command=VENV_ACTIVATE + "python scripts/load_facts.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=DBT_ENV + "dbt run",
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=DBT_ENV + "dbt test",
    )

    # all_done : doit tourner meme si dbt_test a echoue (des tests qui
    # echouent sont precisement le signal le plus utile a faire remonter).
    push_dbt_metrics = BashOperator(
        task_id="push_dbt_metrics",
        bash_command=VENV_ACTIVATE + "python scripts/push_dbt_test_results.py",
        trigger_rule="all_done",
    )
    # Regle par defaut (all_success) : ne marque le pipeline "reussi" que
    # si dbt_test a reellement reussi, pas juste tourne jusqu'au bout.
    push_pipeline_success_task = BashOperator(
        task_id="push_pipeline_success",
        bash_command=VENV_ACTIVATE + "python scripts/push_pipeline_success.py",
    )

    ingest_sources = [ingest_source_a, ingest_source_b, ingest_source_c, ingest_source_d]

    check_sources >> ingest_sources
    ingest_sources >> validate_simple
    validate_simple >> validate_orders
    validate_orders >> [validate_order_items, validate_payments]
    [validate_orders, validate_payments, validate_simple] >> build_dim_date
    [validate_simple, validate_orders] >> load_dimensions
    [build_dim_date, load_dimensions, validate_order_items, validate_payments] >> load_facts
    load_facts >> dbt_run >> dbt_test
    dbt_test >> push_dbt_metrics
    dbt_test >> push_pipeline_success_task
