"""
Génère les 7 domaines de données de RetailFlow dans data/external/,
en y injectant volontairement les défauts décrits dans le cahier des charges
(doublons, nulls, prix incohérents, quantités impossibles, client inexistant,
dates invalides, statut invalide, paiement > commande).

Seed fixe : on doit pouvoir régénérer exactement le même dataset pour
déboguer le pipeline sans que les données changent à chaque run.
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

SEED = 42
OUTPUT_DIR = Path("data/external")

N_CUSTOMERS = 3000
N_PRODUCTS = 400
N_ORDERS = 20000
N_WAREHOUSES = 3

CATEGORIES = {
    "Electronique": ["Sony", "Samsung", "LG", "JBL", "Logitech"],
    "Mode": ["Zara", "Levis", "NewBalance", "Uniqlo"],
    "Maison": ["Ikea", "Tefal", "Moulinex"],
    "Beaute": ["LOreal", "Nivea", "Garnier"],
    "Sport": ["Nike", "Adidas", "Decathlon"],
    "Livres": ["Gallimard", "Hachette", "Flammarion"],
}
COUNTRIES = (
    ["France"] * 6
    + ["Belgique", "Allemagne", "Espagne", "Italie", "Suisse", "Portugal"]
)
ORDER_STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled"]
PAYMENT_METHODS = ["credit_card", "paypal", "bank_transfer"]
PAYMENT_STATUSES = ["success", "failed", "refunded"]
CUSTOMER_SEGMENTS = ["new", "regular", "vip", "at_risk"]

fake = Faker("fr_FR")
Faker.seed(SEED)
random.seed(SEED)


def gen_customers() -> pd.DataFrame:
    rows = []
    for i in range(1, N_CUSTOMERS + 1):
        signup = fake.date_between(start_date="-3y", end_date="today")
        rows.append({
            "customer_id": f"C{i:06d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.unique.email(),
            "country": random.choice(COUNTRIES),
            "city": fake.city(),
            "signup_date": signup.isoformat(),
            "customer_segment": random.choice(CUSTOMER_SEGMENTS),
        })
    return pd.DataFrame(rows)


def gen_products() -> pd.DataFrame:
    rows = []
    cat_names = list(CATEGORIES.keys())
    for i in range(1, N_PRODUCTS + 1):
        cat = random.choice(cat_names)
        unit_cost = round(random.uniform(5, 200), 2)
        rows.append({
            "product_id": f"P{i:05d}",
            "product_name": f"{cat} {fake.word().capitalize()} {i}",
            "category_id": f"CAT-{cat_names.index(cat) + 1}",
            "category_name": cat,
            "brand": random.choice(CATEGORIES[cat]),
            "unit_cost": unit_cost,
            "unit_price": round(unit_cost * random.uniform(1.3, 2.5), 2),
            "stock_threshold": random.randint(10, 50),
        })
    return pd.DataFrame(rows)


def gen_orders(customers: pd.DataFrame) -> pd.DataFrame:
    customer_ids = customers["customer_id"].tolist()
    rows = []
    start = datetime(2026, 1, 1)
    for i in range(1, N_ORDERS + 1):
        order_date = start + timedelta(minutes=random.randint(0, 260 * 24 * 60))
        rows.append({
            "order_id": f"ORD-{i:06d}",
            "customer_id": random.choice(customer_ids),
            "order_date": order_date.isoformat(),
            "order_status": random.choice(ORDER_STATUSES),
            "payment_method": random.choice(PAYMENT_METHODS),
            "shipping_country": random.choice(COUNTRIES),
            "total_amount": 0.0,
        })
    return pd.DataFrame(rows)


def gen_order_items(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    product_rows = products.set_index("product_id")
    rows = []
    item_id = 1
    for order_id in orders["order_id"]:
        for _ in range(random.randint(1, 4)):
            product_id = random.choice(product_rows.index)
            unit_price = float(product_rows.loc[product_id, "unit_price"])
            rows.append({
                "order_item_id": f"OI{item_id:07d}",
                "order_id": order_id,
                "product_id": product_id,
                "quantity": random.randint(1, 5),
                "unit_price": unit_price,
                "discount": round(random.choice([0, 0, 0, 0.1, 0.2]), 2),
            })
            item_id += 1
    return pd.DataFrame(rows)


def compute_totals(orders: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    items = items.copy()
    items["line_total"] = items["quantity"] * items["unit_price"] * (1 - items["discount"])
    totals = items.groupby("order_id")["line_total"].sum().round(2)
    orders = orders.copy()
    orders["total_amount"] = orders["order_id"].map(totals).fillna(0.0)
    return orders


def gen_payments(orders: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i, order in enumerate(orders.itertuples(), start=1):
        rows.append({
            "payment_id": f"PAY{i:06d}",
            "order_id": order.order_id,
            "payment_date": order.order_date,
            "payment_method": order.payment_method,
            "amount": order.total_amount,
            "payment_status": random.choice(PAYMENT_STATUSES),
            "transaction_id": fake.uuid4(),
        })
    return pd.DataFrame(rows)


def gen_returns(items: pd.DataFrame) -> pd.DataFrame:
    sample = items.sample(frac=0.03, random_state=SEED)
    rows = []
    for i, item in enumerate(sample.itertuples(), start=1):
        rows.append({
            "return_id": f"RET{i:05d}",
            "order_id": item.order_id,
            "product_id": item.product_id,
            "return_date": fake.date_between(start_date="-6M", end_date="today").isoformat(),
            "quantity": random.randint(1, max(1, item.quantity)),
            "reason": random.choice(["defectueux", "taille_incorrecte", "change_avis", "non_conforme"]),
        })
    return pd.DataFrame(rows)


def gen_inventory(products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    inv_id = 1
    today = datetime.now().date().isoformat()
    for product_id in products["product_id"]:
        for wh in range(1, N_WAREHOUSES + 1):
            rows.append({
                "inventory_id": f"INV{inv_id:06d}",
                "product_id": product_id,
                "warehouse_id": f"WH-{wh}",
                "snapshot_date": today,
                "stock_quantity": random.randint(0, 500),
            })
            inv_id += 1
    return pd.DataFrame(rows)


def inject_defects(orders: pd.DataFrame, items: pd.DataFrame, payments: pd.DataFrame):
    orders = orders.copy()
    items = items.copy()
    payments = payments.copy()

    dup_rows = orders.sample(n=25, random_state=SEED)
    orders = pd.concat([orders, dup_rows], ignore_index=True)

    idx = orders.sample(n=40, random_state=SEED).index
    orders.loc[idx, "customer_id"] = None

    idx = items.sample(n=30, random_state=SEED).index
    items.loc[idx, "unit_price"] = -abs(items.loc[idx, "unit_price"])

    idx = items.sample(n=30, random_state=SEED + 1).index
    items.loc[idx, "quantity"] = -abs(items.loc[idx, "quantity"])

    idx = orders.sample(n=20, random_state=SEED + 2).index
    orders.loc[idx, "customer_id"] = "C999999"

    idx = orders.sample(n=15, random_state=SEED + 3).index
    orders.loc[idx, "order_date"] = "2026-15-45"

    idx = orders.sample(n=15, random_state=SEED + 4).index
    orders.loc[idx, "order_status"] = "banana"

    idx = payments.sample(n=20, random_state=SEED).index
    payments.loc[idx, "amount"] = payments.loc[idx, "amount"] * 5 + 100

    return orders, items, payments


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    customers = gen_customers()
    products = gen_products()
    orders = gen_orders(customers)
    items = gen_order_items(orders, products)
    orders = compute_totals(orders, items)
    payments = gen_payments(orders)
    returns = gen_returns(items)
    inventory = gen_inventory(products)

    orders, items, payments = inject_defects(orders, items, payments)

    datasets = {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": items,
        "payments": payments,
        "returns": returns,
        "inventory": inventory,
    }
    for name, df in datasets.items():
        path = OUTPUT_DIR / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"{name:15s} -> {len(df):>7,} lignes -> {path}")


if __name__ == "__main__":
    main()
