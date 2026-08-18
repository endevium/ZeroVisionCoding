# AI Accuracy Report (LLM-as-a-Judge)

Evaluated using Groq for subjective metrics.

## Code Review
- **Issue Detection Accuracy:** 35.1%
- **False Positive Rate:** 21.1%
- **Suggestion Quality:** 50.5%
- **Severity Classification Accuracy:** 50.0%
- **Average Response Time:** 19.84s

### Log
- `bare_except.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.50, Severity Classification Accuracy=1.00 (32.5s)
- `broad_exception.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.50, Severity Classification Accuracy=0.00 (18.2s)
- `clean_code.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (17.5s)
- `comparison_is_string.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (37.4s)
- `debug_prints.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (12.8s)
- `division_no_check.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (15.4s)
- `global_mutation.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (16.8s)
- `infinite_loop.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (15.2s)
- `list_concat_loop.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (24.5s)
- `magic_number.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.80, Severity Classification Accuracy=0.50 (25.9s)
- `missing_return.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (11.6s)
- `missing_validation.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (22.9s)
- `mutable_default.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (17.9s)
- `no_docs.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (13.6s)
- `off_by_one.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (25.1s)
- `recursion_no_base.json`: Issue Detection Accuracy=0.33, False Positive Rate=0.00, Suggestion Quality=0.80, Severity Classification Accuracy=1.00 (19.2s)
- `shadow_builtin.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (11.4s)
- `unreachable_return.json`: Issue Detection Accuracy=0.33, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (29.7s)
- `unused_variable.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (9.5s)

