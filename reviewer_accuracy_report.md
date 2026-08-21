# AI Accuracy Report (LLM-as-a-Judge)

Evaluated using Groq for subjective metrics.

## Code Review
- **Issue Detection Accuracy:** 78.9%
- **False Positive Rate:** 10.5%
- **Suggestion Quality:** 47.4%
- **Severity Classification Accuracy:** 68.4%
- **Average Response Time:** 29.70s

### Log
- `bare_except.json`: Issue Detection Accuracy=1.00, False Positive Rate=1.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (85.4s)
- `broad_exception.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (37.4s)
- `clean_code.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (28.0s)
- `comparison_is_string.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (15.9s)
- `debug_prints.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (14.5s)
- `division_no_check.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=1.00 (27.9s)
- `global_mutation.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (20.1s)
- `infinite_loop.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=1.00 (30.5s)
- `list_concat_loop.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (16.0s)
- `magic_number.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (19.0s)
- `missing_return.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (26.8s)
- `missing_validation.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (22.8s)
- `mutable_default.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=1.00 (55.2s)
- `no_docs.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (21.4s)
- `off_by_one.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=0.00 (36.2s)
- `recursion_no_base.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=1.00 (38.0s)
- `shadow_builtin.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (16.1s)
- `unreachable_return.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=1.00 (23.0s)
- `unused_variable.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (30.3s)

