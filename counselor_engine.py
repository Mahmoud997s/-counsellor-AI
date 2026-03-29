import psycopg2
import json

DB_PARAMS = {
    "dbname": "counselor",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5433"
}

def evaluate(rule_logic, facts_state):
    """
    التقييم الآن يعتمد على State كاملة (True/False)
    بدلاً من مجرد البحث العشوائي في قائمة (List)
    """
    rule_if = rule_logic.get("if", [])
    
    # نتحقق أن كل شرط تتطلبه القاعدة موجود وقيمته (True) في حالة القضية الحالية
    if all(facts_state.get(condition, False) for condition in rule_if):
        return rule_logic.get("then", [])
        
    return None

def run_engine(facts_state):
    print(f"Counselor AI Engine started...")
    print("Processing Incoming Case State:")
    print(json.dumps(facts_state, indent=2))
    print("\n")
    
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    cursor.execute("SELECT rule_name, logic, article_id FROM rules;")
    all_rules = cursor.fetchall()
    
    conclusions = []
    
    for rule_name, logic, article_id in all_rules:
        outcome = evaluate(logic, facts_state)
        if outcome:
            cursor.execute("SELECT article_number FROM articles WHERE id = %s;", (article_id,))
            art_num_row = cursor.fetchone()
            art_num = art_num_row[0] if art_num_row else "Unknown"
            
            conclusions.append({
                "rule_name": rule_name,
                "article": art_num,
                "outcome": outcome
            })
            
    cursor.close()
    conn.close()
    
    if conclusions:
        print("🎯 [Decision Reached] Legal Conclusions:")
        for res in conclusions:
            print(f" └─> Applying Article [{res['article']}]: {res['outcome']}")
    else:
        print("🔍 [No Match] The State did not trigger any exact legal rule.")

if __name__ == "__main__":
    # التجربة الجديدة باستخدام الـ State
    test_state = {
      "fault": True,
      "damage": True,
      "intent": False,
      "contract": False
    }
    run_engine(test_state)
