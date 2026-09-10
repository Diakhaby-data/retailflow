import json
import uuid
from pathlib import Path

import pandas as pd

ORDERS_PATH = Path("data/external/orders.csv")
OUTPUT_PATH = Path("data/external/events.jsonl")

def main():
    orders = pd.read_csv(ORDERS_PATH)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for order in orders.itertuples():
            event = {
                "event_id": f"evt_{uuid.uuid4().hex[:12]}",  # identifiant unique de l'evenement
                "event_type": "order_created",
                "timestamp": order.order_date,
                "order_id": order.order_id,
            }
            f.write(json.dumps(event) + "\n")  # \n = un objet JSON par ligne (JSON Lines)

    print(f"{len(orders)} evenements ecrits dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
