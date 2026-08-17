# AI Accuracy Report (LLM-as-a-Judge)

Evaluated using Groq for subjective metrics.

## Code Review
- **Issue Detection Accuracy:** 25.4%
- **False Positive Rate:** 15.8%
- **Suggestion Quality:** 31.6%
- **Severity Classification Accuracy:** 15.8%
- **Average Response Time:** 22.38s

### Log
- `bare_except.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (24.0s)
- `broad_exception.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (14.6s)
- `clean_code.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (10.9s)
- `comparison_is_string.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (7.0s)
- `debug_prints.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (8.8s)
- `division_no_check.json`: Issue Detection Accuracy=0.50, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (24.3s)
- `global_mutation.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (44.9s)
- `infinite_loop.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=0.00 (29.1s)
- `list_concat_loop.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (16.5s)
- `magic_number.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (25.7s)
- `missing_return.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=0.00 (28.9s)
- `missing_validation.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (14.4s)
- `mutable_default.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (25.5s)
- `no_docs.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (33.5s)
- `off_by_one.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (40.7s)
- `recursion_no_base.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (12.3s)
- `shadow_builtin.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (13.4s)
- `unreachable_return.json`: Issue Detection Accuracy=0.33, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=0.00 (38.0s)
- `unused_variable.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (12.4s)

