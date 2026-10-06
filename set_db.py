"""Rebuild the fictional logistics demo tables. No external data is used."""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

# A fixed seed produces the same dataset each time this script runs.
rng = random.Random(42)
start_date = date(2026, 1, 1)
end_date = date(2026, 6, 30)

# Fictional station, region, typical daily packages, failure rate, cost/package.
station_profiles = [
    ("Synthetic Station N01", "North", 4200, 0.025, 3.10),
    ("Synthetic Station N02", "North", 3100, 0.035, 3.35),
    ("Synthetic Station S01", "South", 5200, 0.020, 2.85),
    ("Synthetic Station S02", "South", 3600, 0.040, 3.20),
    ("Synthetic Station E01", "East", 4700, 0.030, 3.00),
    ("Synthetic Station E02", "East", 2800, 0.045, 3.60),
    ("Synthetic Station W01", "West", 5800, 0.022, 2.95),
    ("Synthetic Station W02", "West", 3900, 0.032, 3.25),
]

station_rows = [(i, name, region) for i, (name, region, *_) in enumerate(station_profiles, 1)]
metric_rows = []
cost_rows = []
days = (end_date - start_date).days + 1
for day_number in range(days):
    metric_date = start_date + timedelta(days=day_number)
    progress = day_number / (days - 1)
    # Lower weekend volume and gradual growth across the six months.
    weekend_factor = 0.75 if metric_date.weekday() >= 5 else 1.0
    for station_id, (name, region, base_volume, base_failure, base_cost) in enumerate(station_profiles, 1):
        volume_factor = weekend_factor * (1 + 0.15 * progress)
        total_packages = round(base_volume * volume_factor * rng.uniform(0.88, 1.12))

        # A fictional February disruption makes comparisons more interesting.
        disrupted = region == "East" and date(2026, 2, 10) <= metric_date <= date(2026, 2, 16)
        failure_rate = base_failure * (1 - 0.20 * progress) + rng.uniform(-0.006, 0.006)
        if disrupted:
            failure_rate += 0.04
        failed_packages = round(total_packages * failure_rate)

        # Failed packages cannot be on time; some successful deliveries are late.
        delivered_packages = total_packages - failed_packages
        late_share = rng.uniform(0.01, 0.035) + (0.025 if disrupted else 0)
        on_time_packages = round(delivered_packages * (1 - late_share))
        on_time_pct = round(100 * on_time_packages / total_packages, 2)

        # Packages inducted per operating hour; throughput improves over time.
        induction_rate = round(base_volume / 8 * (1 + 0.10 * progress) * rng.uniform(0.92, 1.08), 2)
        if disrupted:
            induction_rate = round(induction_rate * 0.85, 2)
        total_cost = round(450 + total_packages * base_cost * rng.uniform(0.95, 1.05) + failed_packages * 2.50, 2)
        metric_rows.append((metric_date.isoformat(), station_id, total_packages,
                            failed_packages, on_time_pct, induction_rate))
        cost_rows.append((metric_date.isoformat(), station_id, total_cost))

# Rebuild the three related demo tables together in one transaction.
database_path = Path(__file__).resolve().parent / "database.db"
connection = sqlite3.connect(database_path)
connection.execute("PRAGMA foreign_keys = ON")
try:
    with connection:
        connection.execute("BEGIN")
        # Drop child tables before their parent table.
        connection.execute("DROP TABLE IF EXISTS station_costs")
        connection.execute("DROP TABLE IF EXISTS delivery_metrics")
        connection.execute("DROP TABLE IF EXISTS stations")
        connection.execute("""
            CREATE TABLE stations (
                station_id INTEGER PRIMARY KEY,
                station_name TEXT NOT NULL UNIQUE,
                region TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE delivery_metrics (
                metric_id INTEGER PRIMARY KEY,
                metric_date TEXT NOT NULL,
                station_id INTEGER NOT NULL REFERENCES stations(station_id),
                total_packages INTEGER NOT NULL CHECK (total_packages > 0),
                failed_packages INTEGER NOT NULL CHECK (failed_packages BETWEEN 0 AND total_packages),
                on_time_delivery_pct REAL NOT NULL CHECK (on_time_delivery_pct BETWEEN 0 AND 100),
                induction_rate REAL NOT NULL CHECK (induction_rate > 0),
                UNIQUE (station_id, metric_date)
            )
        """)
        connection.execute("""
            CREATE TABLE station_costs (
                cost_id INTEGER PRIMARY KEY,
                cost_date TEXT NOT NULL,
                station_id INTEGER NOT NULL REFERENCES stations(station_id),
                total_cost REAL NOT NULL CHECK (total_cost >= 0),
                UNIQUE (station_id, cost_date)
            )
        """)
        connection.executemany("INSERT INTO stations VALUES (?, ?, ?)", station_rows)
        connection.executemany("""
            INSERT INTO delivery_metrics (
                metric_date, station_id, total_packages, failed_packages,
                on_time_delivery_pct, induction_rate
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, metric_rows)
        connection.executemany("""
            INSERT INTO station_costs (cost_date, station_id, total_cost)
            VALUES (?, ?, ?)
        """, cost_rows)
finally:
    connection.close()

print(f"Created {len(station_rows)} stations, {len(metric_rows):,} delivery rows, and {len(cost_rows):,} cost rows.")
print(f"Date range: {start_date} through {end_date}. All data is fictional.")
