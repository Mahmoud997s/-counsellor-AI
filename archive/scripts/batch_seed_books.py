import psycopg2
import re
import os

DB_PARAMS = {
    "dbname": "counselor",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5433"
}

BOOKS_TO_SEED = [
    {
        "file": r"c:\Users\DELL\Desktop\قانون\books in txt\clean_الجنائي.txt",
        "domain": "criminal",      
    },
    {
        "file": r"c:\Users\DELL\Desktop\قانون\books in txt\clean_الإجراءات-الجنائية.txt",
        "domain": "criminal_procedure", 
    }
]

def batch_seed():
    print("Connecting to Counselor Database...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    total_inserted = 0
    
    for book in BOOKS_TO_SEED:
        file_path = book["file"]
        domain = book["domain"]
        
        if not os.path.exists(file_path):
            print(f"❌ File not found, skipping: {file_path}")
            continue
            
        print(f"\n📂 Processing Book: {file_path}")
        print(f"📝 Category (law_type): {domain}")
        
        cursor.execute("DELETE FROM articles WHERE domain = %s;", (domain,))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("✂️ Splitting text into individual articles...")
        
        # بسبب التشفير القديم (Presentation Forms) لكتاب الإجراءات الجنائية
        # تم دعم نمط (1 - ﻣﺎﺩﺓ) ونمط (مادة 1) معاً
        split_pattern = r'\n(?=\s*(?:Article|مادة|المادة|ﻣﺎﺩﺓ|ةدام)\s*\[?\s*\d+\s*\]?|.*?\d+\s*[-–]\s*(?:ﻣﺎﺩﺓ|مادة|ةدام))'
        chunks = re.split(split_pattern, content, flags=re.IGNORECASE)
        
        if len(chunks) < 5:
            # Fallback
            chunks = re.split(r'\n(?=.*?\d+\s*[-–])', content)

        inserted_count = 0
        
        for i, text in enumerate(chunks):
            if i == 0 and len(text) > 2000:
                print("Skipping introduction/index section...")
                continue
                
            clean_text = text.strip()
            
            if len(clean_text) > 15:
                # استخراج الرقم من أي نمط
                match = re.search(r'(?:Article|مادة|المادة|ﻣﺎﺩﺓ|ةدام)\s*\[?\s*(\d+[أ-ي]*)\s*\]?|(\d+)\s*[-–]\s*(?:ﻣﺎﺩﺓ|مادة|ةدام)', clean_text, flags=re.IGNORECASE)
                
                if match:
                    article_num = match.group(1) or match.group(2)
                else:
                    article_num = str(inserted_count + 1)
                
                cursor.execute("""
                    INSERT INTO articles (article_number, plain_text, domain)
                    VALUES (%s, %s, %s)
                """, (article_num, clean_text, domain))
                
                inserted_count += 1
                total_inserted += 1
                
        print(f"✅ Inserted {inserted_count} articles for '{domain}' law.")
        
    conn.commit()
    cursor.close()
    conn.close()
    print(f"\n🎉 Batch Seeding Complete! System now hosts {total_inserted} total structured articles.")

if __name__ == "__main__":
    batch_seed()
