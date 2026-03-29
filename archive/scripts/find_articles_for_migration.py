import psycopg2

DB_PARAMS = {
    'dbname': 'counselor',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5433'
}

def identify_conflict_articles():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # We need to find Art 245 (Penal), 91 (Procedure), 15 (Procedure), 62 (Penal), 111 (Child)
        # Since 'law_name' doesn't exist, we search 'plain_text' or 'title' for keywords
        queries = [
            ("245", "دفاع شرعي"),
            ("91", "تفتيش"),
            ("15", "تقادم|انقضاء"),
            ("62", "جنون|عاهة عقيلة"),
            ("111", "طفل|حدث")
        ]
        
        print('--- Searching for Conflict Articles ---')
        for num, keyword in queries:
            cur.execute("""
                SELECT id, article_number, title, LEFT(plain_text, 100) 
                FROM articles 
                WHERE article_number = %s AND (plain_text ~ %s OR title ~ %s)
            """, (num, keyword, keyword))
            rows = cur.fetchall()
            print(f"\nQuery for Art {num} with keyword '{keyword}':")
            for r in rows:
                print(f"  ID: {r[0]} | Title: {r[2]}")
                print(f"  Content: {r[3]}...")
            if not rows:
                print("  No matches found with keywords, searching by number only...")
                cur.execute("SELECT id, article_number, title, LEFT(plain_text, 100) FROM articles WHERE article_number = %s", (num,))
                rows = cur.fetchall()
                for r in rows:
                    print(f"  ID: {r[0]} | Title: {r[2]} | Content: {r[3]}...")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    identify_conflict_articles()
