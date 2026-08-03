# AI Accuracy Report (LLM-as-a-Judge)

Evaluated using Groq for subjective metrics.

## Code Review
- **Issue Detection Accuracy:** 43.5%
- **False Positive Rate:** 14.8%
- **Suggestion Quality:** 55.4%
- **Severity Classification Accuracy:** 54.6%
- **Average Response Time:** 29.15s

### Log
- `bare_except.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.50, Severity Classification Accuracy=1.00 (41.7s)
- `broad_exception.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (11.8s)
- `clean_code.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (19.4s)
- `comparison_is_string.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (36.7s)
- `debug_prints.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (25.7s)
- `division_no_check.json`: Issue Detection Accuracy=0.50, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (24.5s)
- `global_mutation.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (18.8s)
- `infinite_loop.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (22.3s)
- `list_concat_loop.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.67, Suggestion Quality=0.67, Severity Classification Accuracy=0.33 (75.7s)
- `magic_number.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.80, Severity Classification Accuracy=0.50 (33.6s)
- `missing_return.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (17.0s)
- `missing_validation.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (30.1s)
- `mutable_default.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (23.1s)
- `off_by_one.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (39.1s)
- `recursion_no_base.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (31.8s)
- `shadow_builtin.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (15.3s)
- `unreachable_return.json`: Issue Detection Accuracy=0.33, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (33.5s)
- `unused_variable.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (24.5s)

