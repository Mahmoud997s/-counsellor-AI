import psycopg2
import re

DB_PARAMS = {
    "dbname": "counselor",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5433"
}

def seed_db():
    print("Connecting to Database...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    file_path = r"c:\Users\DELL\Desktop\قانون\القانون_المدني_المصري_full.txt"
    print(f"Reading file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Splitting text into articles...")
    # Using a regex boundary that looks for "Article 1", "مادة 1", or "ةدام" (reversed Arabic) at the start of a line.
    # The split keeps the content intact, just isolating blocks between article headers.
    chunks = re.split(r'\n(?=Article\s+\d+|مادة\s*\d+|ةدام)', content, flags=re.IGNORECASE)
    
    if len(chunks) < 50:
        # Fallback if the first split didn't find enough articles
        chunks = re.split(r'\n(?=\d+\s*-)', content)

    print(f"Found approximately {len(chunks)} blocks to insert.")
    inserted_count = 0
    
    # We don't want to insert tiny empty strings
    for i, text in enumerate(chunks):
        clean_text = text.strip()
        if len(clean_text) > 15:
            # Try to grab the article number if it's there
            match = re.search(r'(?:Article|مادة)\s*(\d+)', clean_text, flags=re.IGNORECASE)
            article_num = match.group(1) if match else str(inserted_count + 1)
            
            cursor.execute("""
                INSERT INTO articles (article_number, plain_text, domain)
                VALUES (%s, %s, %s)
            """, (article_num, clean_text, "civil_law"))
            
            inserted_count += 1
            
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Success! {inserted_count} Articles have been safely inserted into the 'articles' table.")

if __name__ == "__main__":
    seed_db()
