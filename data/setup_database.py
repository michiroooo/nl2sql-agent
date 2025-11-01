"""Generate realistic Japanese e-commerce sample data for DuckDB."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pandas as pd

PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
]

FAMILY_NAMES = [
    "佐藤", "鈴木", "高橋", "田中", "伊藤", "渡辺", "山本", "中村", "小林", "加藤",
    "吉田", "山田", "佐々木", "山口", "松本", "井上", "木村", "林", "斎藤", "清水"
]

GIVEN_NAMES = [
    "太郎", "花子", "一郎", "美咲", "健太", "さくら", "大輔", "由美", "翔太", "愛",
    "隼人", "葵", "拓也", "結衣", "航", "陽菜", "蓮", "凛", "悠斗", "咲"
]

PRODUCTS = {
    "電化製品": [
        ("ノートパソコン", 89800),
        ("スマートフォン", 78900),
        ("タブレット", 45600),
        ("ワイヤレスイヤホン", 12800),
        ("スマートウォッチ", 34500),
        ("デジタルカメラ", 67800),
        ("ポータブルSSD", 15900),
        ("モニター", 28900),
        ("キーボード", 8900),
        ("マウス", 3980),
    ],
    "書籍": [
        ("ビジネス書", 1980),
        ("技術書", 3980),
        ("小説", 1650),
        ("漫画", 550),
        ("料理本", 1780),
        ("旅行ガイド", 1980),
        ("自己啓発本", 1650),
        ("歴史書", 2980),
        ("絵本", 1280),
        ("雑誌", 890),
    ],
    "食品・飲料": [
        ("有機野菜セット", 2980),
        ("プレミアムコーヒー", 1580),
        ("ナッツミックス", 980),
        ("オリーブオイル", 1280),
        ("はちみつ", 1680),
        ("調味料セット", 2480),
        ("お菓子詰め合わせ", 1980),
        ("緑茶", 980),
        ("ミネラルウォーター", 580),
        ("インスタント食品", 780),
    ],
}


def generate_customers(n: int = 200) -> pd.DataFrame:
    """Generate customer data with Japanese names and prefectures."""
    data = {
        "customer_id": range(1, n + 1),
        "customer_name": [
            f"{random.choice(FAMILY_NAMES)} {random.choice(GIVEN_NAMES)}"
            for _ in range(n)
        ],
        "prefecture": [random.choice(PREFECTURES) for _ in range(n)],
        "registration_date": [
            datetime(2023, 1, 1) + timedelta(days=random.randint(0, 730))
            for _ in range(n)
        ],
    }
    return pd.DataFrame(data)


def generate_products() -> pd.DataFrame:
    """Generate product catalog with realistic Japanese items."""
    rows = []
    product_id = 1

    for category, items in PRODUCTS.items():
        for name, price in items:
            rows.append({
                "product_id": product_id,
                "product_name": name,
                "category": category,
                "price": price,
                "stock_quantity": random.randint(5, 100),
            })
            product_id += 1

    return pd.DataFrame(rows)


def generate_orders(
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame,
    n: int = 1000,
) -> pd.DataFrame:
    """Generate order history with realistic transaction patterns."""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 10, 31)
    date_range = (end_date - start_date).days

    rows = []
    for order_id in range(1, n + 1):
        customer = customers_df.sample(1).iloc[0]
        product = products_df.sample(1).iloc[0]
        quantity = random.randint(1, 5)

        rows.append({
            "order_id": order_id,
            "customer_name": customer["customer_name"],
            "product_id": product["product_id"],
            "quantity": quantity,
            "order_date": start_date + timedelta(days=random.randint(0, date_range)),
            "total_amount": product["price"] * quantity,
        })

    return pd.DataFrame(rows)


def main() -> None:
    """Create DuckDB database with sample data."""
    db_path = Path(__file__).parent / "ecommerce.db"

    customers = generate_customers(200)
    products = generate_products()
    orders = generate_orders(customers, products, 1000)

    conn = duckdb.connect(str(db_path))

    conn.execute("DROP TABLE IF EXISTS customers")
    conn.execute("DROP TABLE IF EXISTS products")
    conn.execute("DROP TABLE IF EXISTS orders")

    conn.execute("CREATE TABLE customers AS SELECT * FROM customers")
    conn.execute("CREATE TABLE products AS SELECT * FROM products")
    conn.execute("CREATE TABLE orders AS SELECT * FROM orders")

    print(f"Database created at: {db_path}")
    print(f"Customers: {len(customers)}")
    print(f"Products: {len(products)}")
    print(f"Orders: {len(orders)}")

    print("\n=== Sample Data ===")
    print("\nCustomers (first 5):")
    print(conn.execute("SELECT * FROM customers LIMIT 5").df())
    print("\nProducts (first 5):")
    print(conn.execute("SELECT * FROM products LIMIT 5").df())
    print("\nOrders (first 5):")
    print(conn.execute("SELECT * FROM orders LIMIT 5").df())

    conn.close()


if __name__ == "__main__":
    main()
