import psycopg2

DB_PARAMS = {
    'dbname': 'counselor',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5433'
}

def find_target_articles():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # We need Art 245 (Penal), 91 (Procedure), 15 (Procedure), 62 (Penal), 111 (Child)
        targets = [
            ("245", "دفاع شرعي"),
            ("91", "تفتيش|بطلان"),
            ("15", "تقادم|انقضاء"),
            ("62", "جنون|إدراك"),
            ("111", "طفل|حدث")
        ]
        
        print("--- Target Articles Search ---")
        for num, keyword in targets:
            cur.execute("""
                SELECT id, article_number, LEFT(plain_text, 120) 
                FROM articles 
                WHERE article_number = %s AND plain_text ~ %s
            """, (num, keyword))
            rows = cur.fetchall()
            print(f"\nSearching Art {num} with '{keyword}':")
            for r in rows:
                print(f"  ID: {r[0]} | Content: {r[2]}...")
            if not rows:
                # Fallback to number only
                cur.execute("SELECT id, article_number, LEFT(plain_text, 60) FROM articles WHERE article_number = %s LIMIT 5", (num,))
                rows = cur.fetchall()
                print(f"  [Fallback] Matches for Art {num}:")
                for r in rows:
                    print(f"    ID: {r[0]} | Content: {r[2]}...")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_target_articles()
