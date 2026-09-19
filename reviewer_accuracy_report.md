# AI Accuracy Report (LLM-as-a-Judge)

Evaluated using Groq for subjective metrics.

## Code Debugging (Fixer)
- **Error Detection Accuracy:** 75.0%
- **Fix Success Rate:** 91.7%
- **Runtime Success Rate:** 75.0%
- **Logic Preservation Rate:** 71.5%
- **Average Response Time:** 18.70s

### Log
- `assertion_error.json`: Error Detection Accuracy=0.00, Fix Success Rate=0.00, Runtime Success Rate=0.00, Logic Preservation Rate=0.00 (24.7s)
- `attribute_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (14.0s)
- `call_none.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.50 (17.9s)
- `empty_pop.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=0.00 (18.7s)
- `file_not_found.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=0.00 (50.4s)
- `float_division_zero.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (17.8s)
- `indentation_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (19.1s)
- `index_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (18.8s)
- `int_subscript.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (16.6s)
- `key_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.70 (17.1s)
- `list_index_negative.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=1.00 (16.9s)
- `module_not_found.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=0.00 (12.6s)
- `name_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (14.0s)
- `nested_key_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (15.7s)
- `none_append.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (15.3s)
- `recursion_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.95 (19.5s)
- `syntax_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (12.7s)
- `type_error_args.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (18.5s)
- `type_error_concat.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (15.9s)
- `unbound_local.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (18.7s)
- `unpack_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (15.9s)
- `value_error.json`: Error Detection Accuracy=0.00, Fix Success Rate=0.00, Runtime Success Rate=0.00, Logic Preservation Rate=1.00 (19.4s)
- `wrong_function_usage.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (21.0s)
- `zero_division.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (17.9s)

