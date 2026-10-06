"""
Marque le pipeline comme ayant reussi de bout en bout. Appelee avec la
regle de declenchement par defaut (all_success) : n'est atteinte que si
dbt_test a reellement reussi, contrairement a push_dbt_test_results qui
tourne toujours.
"""
from src.monitoring.metrics import push_pipeline_success

if __name__ == "__main__":
    push_pipeline_success()
