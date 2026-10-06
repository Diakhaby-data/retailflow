#!/bin/bash
set -euo pipefail

echo "Verification de la base de metadonnees 'airflow'..."
# Le mecanisme docker-entrypoint-initdb.d de l'image postgres ne tourne
# qu'a la toute premiere initialisation d'un volume vide. Le volume
# retailflow_pgdata existe deja (il contient la base 'retailflow'), donc
# il faut creer la base 'airflow' nous-memes, de facon idempotente.
EXISTS=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h postgres -U "$POSTGRES_USER" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='airflow'")

if [ "$EXISTS" != "1" ]; then
    echo "Base 'airflow' absente, creation..."
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h postgres -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE airflow"
else
    echo "Base 'airflow' deja presente."
fi

echo "Synchronisation des dependances dans le venv principal..."
# Le venv principal vit dans un volume Docker nomme, persistant : il n'est
# peuple depuis l'image qu'a la toute premiere creation du volume, jamais
# aux demarrages suivants. Si requirements.txt change apres coup (nouvelle
# dependance ajoutee), ce volume existant ne le sait pas tant qu'on ne
# relance pas explicitement pip install ici. Idempotent et rapide si rien
# n'a change : pip ne reinstalle que ce qui manque ou a change de version.
/home/dkb/ecommerce/venv/bin/pip install --no-cache-dir -r requirements.txt -q

echo "Installation du projet en mode editable dans le venv principal..."
# Meme logique pour le lien vers src/ : src/ n'existe pas au moment du
# build de l'image (seul requirements.txt y est encore), il arrive plus
# tard via le bind mount. --no-deps car les dependances viennent d'etre
# traitees juste au-dessus.
/home/dkb/ecommerce/venv/bin/pip install --no-cache-dir -e . --no-deps -q

# Activer le venv (plutot qu'appeler l'executable par chemin absolu) met
# a jour PATH pour toute la suite du script. C'est indispensable ici :
# "airflow standalone" lance lui-meme scheduler/dag-processor/api-server/
# triggerer comme sous-processus via Popen(['airflow', ...]), sans chemin
# absolu, donc ces sous-processus heritent de ce PATH pour retrouver la
# commande "airflow".
source /home/dkb/ecommerce/airflow_venv/bin/activate
exec airflow standalone
