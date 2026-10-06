# AI SQL Analytics Assistant

A simple Streamlit chat app that generates SQL from a business question, validates it, queries SQLite in read-only mode, and explains the result.

## Run locally

1. Install dependencies: `python -m pip install -r requirement.txt`
2. Copy `.env.example` to `.env` and enter your own OpenAI API key.
3. Run `python set_db.py` to create the synthetic logistics dataset. Each run recreates `stations`, `delivery_metrics`, and `station_costs` with the same sample data; unrelated tables are untouched.
4. Start the app: `python -m streamlit run app.py`

Try asking: "Which station has the highest failure rate?"

The answer appears in chat. Expand **View details** to see the SQL and raw result.

## Synthetic logistics demo

All records are generated locally from fictional assumptions, with no real company or confidential data. A fixed random seed makes the demo repeatable.

The dataset covers **8 fictional stations** in **4 regions**, with **181 days** from **January 1 through June 30, 2026**. The generated values include weekend volume reductions, gradual growth and efficiency improvements, and a fictional East-region disruption on February 10-16. These are invented demonstration patterns, not real operational measurements.

| Table | Rows | One row represents |
| --- | --- | --- |
| `stations` | 8 | One fictional station |
| `delivery_metrics` | 1,448 | One station's delivery metrics for one day |
| `station_costs` | 1,448 | One station's operating cost for one day |

| Table | Columns and meanings |
| --- | --- |
| `stations` | `station_id`: primary key; `station_name`: fictional display name; `region`: North, South, East, or West |
| `delivery_metrics` | `metric_id`: primary key; `metric_date`: YYYY-MM-DD; `station_id`: foreign key; `total_packages`: attempted packages including failures; `failed_packages`: packages not delivered; `on_time_delivery_pct`: percentage of all attempted packages delivered on time (0-100); `induction_rate`: packages inducted per operating hour |
| `station_costs` | `cost_id`: primary key; `cost_date`: YYYY-MM-DD; `station_id`: foreign key; `total_cost`: daily operating cost in fictional USD |

Both daily tables reference `stations.station_id`. Foreign keys are enforced during setup, and each daily table allows only one row per station/date.

When combining deliveries and costs, match **both station and date**. Matching only station would count each day's deliveries against every day's cost and inflate totals. The independent `metric_id` and `cost_id` values are not join keys.

```sql
SELECT s.station_name,
       ROUND(SUM(c.total_cost) / SUM(d.total_packages), 2) AS cost_per_package_usd
FROM stations s
JOIN delivery_metrics d ON d.station_id = s.station_id
JOIN station_costs c
  ON c.station_id = d.station_id AND c.cost_date = d.metric_date
GROUP BY s.station_id, s.station_name
ORDER BY cost_per_package_usd;
```

Failure rates are calculated from summed failures divided by summed packages. Overall on-time percentages are package-weighted and approximate because daily percentages are rounded. Cost per package uses summed cost divided by summed packages. Average induction rate is an unweighted average of daily rates, not an overall throughput rate.

Example questions:

- How did total package volume change by month?
- Compare cost per package across regions using delivery volumes and operating costs.
- Show monthly package volume and total operating cost by region.
- Rank stations by failure rate in June 2026.
- Which region had the lowest on-time delivery percentage in February?
- What was the average daily induction rate for each station?
- How many packages were attempted and failed during the full period?

Run `python check_data.py` to inspect row counts, foreign-key integrity, dates, and a three-table JOIN summary. The AI SQL validation and read-only execution flow remain in place.

## Credentials and data

The API key and local database are excluded from Git by `.gitignore`. Never upload your `.env` file. The shared code contains no API key; running the AI features requires your own key.
