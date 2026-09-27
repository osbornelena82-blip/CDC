#AI helped me query what I wanted from the API

import duckdb
import datetime
import os

duckdb.sql("SET s3_endpoint='storage.googleapis.com'")
duckdb.sql("PRAGMA enable_progress_bar")

details_bucket_path = (
    "gs://noaa-ncei-ipg/notebooks/data/stormevents/"
    "storm_events_database_details/*/*.parquet"
)

current_year = datetime.date.today().year

print("Running sanity check on last year's data...")
test = duckdb.sql(f"""
    SELECT COUNT(*) AS n
    FROM read_parquet('{details_bucket_path}',
                       hive_partitioning=true, union_by_name=true) AS details
    WHERE details.EVENT_TYPE = 'Tornado'
      AND details.YEAR = {current_year - 1}
""").to_df()
print("Sanity check, tornadoes last year:", test)

query = f"""
    SELECT *
    FROM read_parquet('{details_bucket_path}',
                       hive_partitioning=true, union_by_name=true) AS details
    WHERE details.EVENT_TYPE = 'Tornado'
      AND details.YEAR BETWEEN 1986 AND {current_year}
      AND details.TOR_F_SCALE IN ('F3', 'F4', 'F5', 'EF3', 'EF4', 'EF5')
"""

cache_path = os.path.expanduser("~/tornadoes_1986_present_f3plus_cache.parquet")

if os.path.exists(cache_path):
    print("Loading from local cache, skipping network query...")
    tornadoes = duckdb.sql(f"SELECT * FROM read_parquet('{cache_path}')")
    tornadoes_df = tornadoes.to_df()
else:
    print("Running full 1986-present query (F3+), this may take several minutes...")
    tornadoes = duckdb.sql(query)
    tornadoes_df = tornadoes.to_df()
    tornadoes.write_parquet(cache_path)
    print("Query finished, cached locally to", cache_path)

print("Tornado records loaded:", tornadoes_df.shape[0])
print(tornadoes_df.head())

output_path = os.path.expanduser("~/tornadoes_1986_present_f3plus.csv")
tornadoes.write_csv(output_path)
print("Saved to", output_path)