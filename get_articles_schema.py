import psycopg2

DB_PARAMS = {
    'dbname': 'counselor',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5433'
}

def get_schema():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'articles'")
    rows = cur.fetchall()
    print("--- Articles Table Schema ---")
    for row in rows:
        print(f"Column: {row[0]} | Type: {row[1]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    get_schema()
