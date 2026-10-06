# RetailFlow · Plateforme data e-commerce de bout en bout

![CI](https://github.com/Diakhaby-data/retailflow/actions/workflows/ci.yml/badge.svg)

RetailFlow est un projet portfolio qui simule la plateforme data d'un site e-commerce : ingestion depuis plusieurs sources heterogenes, controle qualite, entrepot de donnees en modele en etoile, transformation avec dbt, exposition via une API, et supervision par Prometheus/Grafana. Le tout est orchestre par Apache Airflow, conteneurise avec Docker, et valide automatiquement a chaque push par une CI GitHub Actions qui rejoue le pipeline complet sur une base de donnees ephemere.

## Architecture

Quatre sources simulent des systemes reels distincts, exactement comme on en trouve dans une entreprise (un ERP, une API de catalogue, des exports CSV d'un outil tiers, un flux d'evenements applicatifs) :

| Source | Nature | Contenu |
|---|---|---|
| A | Base PostgreSQL | commandes, lignes de commande, paiements |
| B | API REST (mock FastAPI) | catalogue produits, categories |
| C | Fichiers CSV | clients, retours, inventaire |
| D | Flux JSON Lines | evenements `order_created` |

Pipeline, de la source au tableau de bord :

1. **Ingestion** (`scripts/ingest_*.py`) : chaque source est lue avec le client adapte (SQLAlchemy, `requests`, `pandas.read_csv`, lecture ligne a ligne) et ecrite en Parquet dans un data lake local, partitionne par date d'ingestion.
2. **Qualite des donnees** (`scripts/validate_*.py`) : regles metier appliquees avec pandas (doublons, valeurs nulles, incoherences de prix ou de quantite, cles etrangeres orphelines). Chaque run pousse ses metriques de conformite vers un Prometheus Pushgateway.
3. **Entrepot** (`scripts/build_dim_date.py`, `load_dimensions.py`, `load_facts.py`) : chargement dans un schema PostgreSQL `dwh` modelise en etoile (dimensions clients, produits, date, entrepots ; faits commandes, lignes, paiements, retours, inventaire).
4. **Transformation** (dbt, dossier `transform/`) : modeles `staging` (vues de nettoyage) puis `marts` (tables agregees, pretes a l'usage analytique), avec tests dbt sur chaque run.
5. **Orchestration** : un DAG Airflow quotidien (`airflow/dags/retailflow_pipeline.py`, 16 taches) enchaine ces etapes avec gestion explicite des dependances et des regles de declenchement.
6. **Exposition** : une API FastAPI sert les donnees des marts ; un dashboard Grafana affiche la sante du pipeline (volumes ingeres, taux de qualite, resultats des tests dbt) et les metriques de l'API (latence, taux d'erreur, trafic par route).
7. **CI/CD** : un workflow GitHub Actions rejoue l'integralite de cette chaine (etapes 1 a 4, plus la suite de tests) sur un service PostgreSQL et un Pushgateway ephemeres a chaque push, puis verifie que les deux images Docker du projet se construisent sans erreur.

## Stack technique

| Domaine | Outils |
|---|---|
| Langage | Python 3.12, SQL |
| Traitement de donnees | pandas, SQLAlchemy, psycopg2 |
| Entrepot | PostgreSQL (schema `dwh`, modele en etoile) |
| Transformation | dbt |
| Orchestration | Apache Airflow |
| API | FastAPI |
| Monitoring | Prometheus, Prometheus Pushgateway, Grafana |
| Conteneurisation | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Tests | pytest (unitaires et integration) |

## Lancer le projet en local

Prerequis : Docker et Docker Compose installes.

```bash
git clone https://github.com/Diakhaby-data/retailflow.git
cd retailflow
cp .env.example .env
docker compose up -d --build
```

Services accessibles une fois les conteneurs demarres :

| Service | URL |
|---|---|
| Interface Airflow | http://localhost:8085 |
| API | http://localhost:8001 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

Le DAG `retailflow_pipeline` se declenche depuis l'interface Airflow. Les dashboards Grafana (API et pipeline) sont provisionnes automatiquement au demarrage.

## API

Quelques endpoints exposes par l'API (voir `api/main.py` pour la liste complete) :

| Endpoint | Description |
|---|---|
| `GET /customers` | liste des clients |
| `GET /customers/{id}` | detail d'un client |
| `GET /customers/segment/{segment}` | clients par segment |
| `GET /sales` | ventes agregees |
| `GET /sales/pays/{country}` | ventes par pays |
| `GET /sales/categorie/{category}` | ventes par categorie de produit |
| `GET /inventory` | etat du stock |
| `GET /inventory/{id}` | detail d'un article en stock |
| `GET /inventory/statut/{status}` | stock filtre par statut |
| `GET /dashboard` | indicateurs agreges pour un tableau de bord |

## Tests

```bash
pytest -v
```

La suite est divisee en deux :

- `tests/unit/` : tests unitaires, sans dependance externe.
- `tests/integration/` : tests d'integration qui tournent contre une vraie base PostgreSQL deja peuplee (les marts doivent etre a jour, donc un `dbt run` prealable est necessaire en local).

## CI/CD

Le workflow (`.github/workflows/ci.yml`) se declenche a chaque push ou pull request sur `main`. Il demarre des services PostgreSQL et Pushgateway ephemeres, rejoue l'integralite du pipeline (generation des donnees, ingestion des 4 sources, validation qualite, chargement de l'entrepot, `dbt run`, `dbt test`), execute la suite `pytest` complete, puis verifie que les images Docker du projet (`Dockerfile.app`, `Dockerfile.airflow`) se construisent sans erreur.

## Auteur

Mamadou Diakhaby, data engineer.
