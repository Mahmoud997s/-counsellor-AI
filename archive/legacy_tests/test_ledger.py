import sys
import os
sys.path.append(os.getcwd())
from case_analyzer import analyze_case

# T36: Narrative Contradiction Test
# 1. Victim killed (is_victim_dead = True)
# 2. Search shows no weapon (victim_was_unarmed = True)
# 3. Defendant claims self-defense later.

case_text = """
في يوم ١٠ قام المتهم بقتل الضحية عمداً بطلق ناري.
وبالبحث والتفتيش لم يتم العثور على أي أسلحة مع الضحية.
وفي اليوم التالي ادعى المتهم أنه كان في حالة دفاع شرعي لأن الضحية هاجمه بسكين.
"""

print("Running T36: Narrative Contradiction Test (v3.3)")
result = analyze_case(case_text, debug=True)
print("\nFinal Verdict:", result["verdict"])
