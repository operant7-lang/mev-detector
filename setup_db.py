import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("SUPABASE_HOST"),
    port=os.getenv("SUPABASE_PORT"),
    dbname=os.getenv("SUPABASE_DB"),
    user=os.getenv("SUPABASE_USER"),
    password=os.getenv("SUPABASE_PASSWORD")
)

cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS mev_sandwiches (
        id SERIAL PRIMARY KEY,
        block_number INTEGER,
        block_timestamp INTEGER,
        frontrun_tx TEXT,
        victim_tx TEXT,
        backrun_tx TEXT,
        bot_address TEXT,
        victim_address TEXT,
        token_address TEXT,
        extracted_eth NUMERIC,
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.commit()
conn.close()
print("MEV table created successfully")