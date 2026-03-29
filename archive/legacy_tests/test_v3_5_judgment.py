import sys
import os
sys.path.append(os.getcwd())
from case_analyzer import analyze_case

# Case X: Multi-event with contradictions and legal defenses
case_text = "في يوم 10، هجم س على ص بسكين ليقتله فدافع ص عن نفسه وقتله. وفي يوم 11، دخلت الشرطة منزل ص وفتشته دون إذن فوجدت مخدرات. وفي يوم 12، عاد س للحراسة وضرب ص ولكن تبين أن س كان قد مات فعلاً في يوم 10."

print("🧪 Testing Judicial Language Engine (v3.5)")
print("==========================================")
result = analyze_case(case_text)

print("\n📜 Final Verdict Summary:", result["verdict"])
print("\n⚖️ FULL JUDICIAL JUDGMENT:")
print("-" * 30)
print(result["judicial_judgment"])
print("-" * 30)
