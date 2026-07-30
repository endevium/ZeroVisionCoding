# AI Accuracy Report (LLM-as-a-Judge)

Evaluated using Groq for subjective metrics.

## Code Review
- **Issue Detection Accuracy:** 19.3%
- **False Positive Rate:** 15.8%
- **Suggestion Quality:** 33.2%
- **Severity Classification Accuracy:** 36.8%
- **Average Response Time:** 37.28s

### Log
- `bare_except.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.50, Severity Classification Accuracy=1.00 (54.6s)
- `broad_exception.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.50, Severity Classification Accuracy=1.00 (32.6s)
- `clean_code.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (29.5s)
- `comparison_is_string.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (22.3s)
- `debug_prints.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (49.0s)
- `division_no_check.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (46.0s)
- `global_mutation.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (45.6s)
- `infinite_loop.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (40.1s)
- `list_concat_loop.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (38.0s)
- `magic_number.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (38.3s)
- `missing_return.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (34.6s)
- `missing_validation.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (30.9s)
- `mutable_default.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (34.8s)
- `no_docs.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (31.2s)
- `off_by_one.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.50, Severity Classification Accuracy=0.00 (47.1s)
- `recursion_no_base.json`: Issue Detection Accuracy=0.33, False Positive Rate=0.00, Suggestion Quality=0.80, Severity Classification Accuracy=1.00 (40.2s)
- `shadow_builtin.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (28.1s)
- `unreachable_return.json`: Issue Detection Accuracy=0.33, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (40.7s)
- `unused_variable.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (24.9s)

