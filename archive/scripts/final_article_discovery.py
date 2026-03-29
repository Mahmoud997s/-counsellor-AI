import psycopg2

DB_PARAMS = {
    'dbname': 'counselor',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5433'
}

def find_conflict_articles():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # Specific search terms for the classic conflict rules
        searches = [
            ("245", "دفاع شرعي"), # Penal Code Art 245
            ("91", "تفتيش|بطلان"), # Criminal Procedure Art 91
            ("15", "تقادم|انقضاء"), # Criminal Procedure Art 15
            ("62", "جنون|إدراك"),   # Penal Code Art 62
            ("111", "طفل|حدث")     # Child Law Art 111
        ]
        
        print("--- Final Conflict Article Search ---")
        for num, regex in searches:
            cur.execute("""
                SELECT id, article_number, LEFT(plain_text, 200) 
                FROM articles 
                WHERE article_number = %s AND plain_text ~ %s
            """, (num, regex))
            rows = cur.fetchall()
            print(f"\nArt {num} (Regex: {regex}):")
            for r in rows:
                print(f"  ID: {r[0]}")
                print(f"  Content: {r[2]}...")
            if not rows:
                print("  No direct match found. Will require manual seeding if missing.")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_conflict_articles()
