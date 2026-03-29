import psycopg2

DB_PARAMS = {
    "dbname": "counselor",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5433"
}

conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

# اجيب 30 مادة جنائية مختلفة لنفهم patterns النص
cur.execute("""
    SELECT article_number, plain_text 
    FROM articles 
    WHERE domain = 'criminal'
    AND article_number ~ '^[0-9]+$'
    AND article_number::int BETWEEN 200 AND 350
    ORDER BY article_number::int
    LIMIT 30;
""")
rows = cur.fetchall()
for num, text in rows:
    print(f"\n--- مادة {num} ---")
    print(text[:400])
    print("...")

cur.close()
conn.close()
