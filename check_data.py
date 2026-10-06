"""Inspect the fictional dataset and its relationships without changing data."""
import sqlite3
from pathlib import Path

database_path = Path(__file__).resolve().parent / "database.db"
connection = sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True)
try:
    for table in ("stations", "delivery_metrics", "station_costs"):
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count:,} rows")
    print("Foreign key problems (should be empty):", connection.execute("PRAGMA foreign_key_check").fetchall())
    print("Date range:", connection.execute("SELECT MIN(metric_date), MAX(metric_date) FROM delivery_metrics").fetchone())
    print("\nStation, region, packages, failures, cost (USD), cost per package (USD):")
    # Both station and date are needed to avoid counting costs repeatedly.
    for row in connection.execute("""
        SELECT s.station_name, s.region, SUM(d.total_packages), SUM(d.failed_packages),
               ROUND(SUM(c.total_cost), 2),
               ROUND(SUM(c.total_cost) / SUM(d.total_packages), 2)
        FROM stations s
        JOIN delivery_metrics d ON d.station_id = s.station_id
        JOIN station_costs c ON c.station_id = d.station_id AND c.cost_date = d.metric_date
        GROUP BY s.station_id, s.station_name, s.region
        ORDER BY s.station_id
    """):
        print(row)
finally:
    connection.close()
