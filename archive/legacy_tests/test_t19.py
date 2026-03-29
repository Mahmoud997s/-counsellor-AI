import sys
import os
sys.path.append(os.getcwd())
from case_analyzer import analyze_case

# T19: Global Override Robustness
case_text = "عاد المتهم ليلاً مع عصابة وسرقوا المحل وضربوا الحارس ولكن تبين وجود حالة ضرورة قصوى"

print("Running T19: Global Override Robustness (v3.4)")
result = analyze_case(case_text, debug=True)
print("\nFinal Verdict:", result["verdict"])
# print("Final Summary:", result["final_summary"]) # result["verdict"] contains the summary
