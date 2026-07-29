# AI Accuracy Report (LLM-as-a-Judge)

Evaluated using Groq for subjective metrics.

## Code Debugging (Fixer)
- **Error Detection Accuracy:** 54.2%
- **Fix Success Rate:** 100.0%
- **Runtime Success Rate:** 83.3%
- **Logic Preservation Rate:** 45.8%
- **Average Response Time:** 8.20s

### Log
- `assertion_error.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (11.4s)
- `attribute_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (6.8s)
- `call_none.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (7.8s)
- `empty_pop.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (8.9s)
- `file_not_found.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=1.00 (11.5s)
- `float_division_zero.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (7.0s)
- `indentation_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (6.5s)
- `index_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (6.9s)
- `int_subscript.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (9.6s)
- `key_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (8.3s)
- `list_index_negative.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=0.00 (7.8s)
- `module_not_found.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=0.00 (7.1s)
- `name_error.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (7.5s)
- `nested_key_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (7.7s)
- `none_append.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (7.9s)
- `recursion_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (9.2s)
- `syntax_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (5.0s)
- `type_error_args.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (9.1s)
- `type_error_concat.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=0.00 (8.6s)
- `unbound_local.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (9.5s)
- `unpack_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (9.8s)
- `value_error.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (8.2s)
- `wrong_function_usage.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (8.3s)
- `zero_division.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (6.4s)

## Code Review
- **Issue Detection Accuracy:** 5.3%
- **False Positive Rate:** 0.0%
- **Suggestion Quality:** 5.3%
- **Severity Classification Accuracy:** 5.3%
- **Average Response Time:** 5.74s

### Log
- `bare_except.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (12.8s)
- `broad_exception.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.2s)
- `clean_code.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (5.3s)
- `comparison_is_string.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.3s)
- `debug_prints.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.4s)
- `division_no_check.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.3s)
- `global_mutation.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.5s)
- `infinite_loop.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.2s)
- `list_concat_loop.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.2s)
- `magic_number.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.3s)
- `missing_return.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.9s)
- `missing_validation.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.4s)
- `mutable_default.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.5s)
- `no_docs.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.3s)
- `off_by_one.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.4s)
- `recursion_no_base.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.2s)
- `shadow_builtin.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.2s)
- `unreachable_return.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.3s)
- `unused_variable.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (5.5s)

## Analyze Code
- **Analysis Accuracy:** 91.6%
- **Logic Explanation Accuracy:** 95.0%
- **Issue Detection Rate:** 0.0%
- **Suggestion Relevance:** 0.0%
- **Average Response Time:** 12.60s

### Log
- `anagram_check.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (16.8s)
- `average_grade.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (9.7s)
- `binary_search.json`: Analysis Accuracy=0.80, Logic Explanation Accuracy=0.90, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (18.7s)
- `bubble_sort.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.80, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (10.5s)
- `calculator.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (14.5s)
- `celsius_to_fahrenheit.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.90, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (9.2s)
- `class_student.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (11.6s)
- `factorial_iterative.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (10.2s)
- `fibonacci.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (14.7s)
- `file_counter.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (12.1s)
- `find_largest.json`: Analysis Accuracy=1.00, Logic Explanation Accuracy=1.00, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (12.9s)
- `fizzbuzz.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (16.2s)
- `json_parse.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (8.3s)
- `linear_search.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (11.1s)
- `list_comprehension.json`: Analysis Accuracy=1.00, Logic Explanation Accuracy=1.00, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (9.8s)
- `matrix_transpose.json`: Analysis Accuracy=1.00, Logic Explanation Accuracy=1.00, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (12.0s)
- `merge_dicts.json`: Analysis Accuracy=1.00, Logic Explanation Accuracy=1.00, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (7.2s)
- `palindrome_check.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (8.6s)
- `prime_check.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (9.3s)
- `read_csv.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (22.5s)
- `remove_duplicates.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (12.7s)
- `running_average.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (13.9s)
- `stack_implementation.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (15.9s)
- `sum_digits.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (13.5s)
- `word_frequency.json`: Analysis Accuracy=1.00, Logic Explanation Accuracy=1.00, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (13.3s)

## Explain Code
- **Explanation Accuracy:** 92.5%
- **Context Awareness:** 60.4%
- **Terminology Correctness:** 93.1%
- **Completeness:** 77.1%
- **Average Response Time:** 4.52s

### Log
- `class_animal.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (7.2s)
- `class_method.json`: Explanation Accuracy=0.90, Context Awareness=0.60, Terminology Correctness=0.90, Completeness=0.70 (2.2s)
- `context_manager.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (4.4s)
- `count_vowels.json`: Explanation Accuracy=1.00, Context Awareness=0.00, Terminology Correctness=1.00, Completeness=1.00 (5.2s)
- `decimal_format.json`: Explanation Accuracy=1.00, Context Awareness=0.00, Terminology Correctness=1.00, Completeness=0.00 (1.8s)
- `decorator.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (6.8s)
- `dict_comprehension.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (3.5s)
- `filter_even.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (4.6s)
- `for_loop_sum.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (6.3s)
- `generator.json`: Explanation Accuracy=0.80, Context Awareness=0.40, Terminology Correctness=0.90, Completeness=0.70 (6.8s)
- `get_age.json`: Explanation Accuracy=1.00, Context Awareness=0.50, Terminology Correctness=1.00, Completeness=0.80 (3.4s)
- `lambda_sort.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (5.6s)
- `list_comprehension.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (3.1s)
- `main_function.json`: Explanation Accuracy=0.80, Context Awareness=0.60, Terminology Correctness=0.90, Completeness=0.70 (3.4s)
- `map_lambda.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (2.6s)
- `normalize_name.json`: Explanation Accuracy=1.00, Context Awareness=0.00, Terminology Correctness=1.00, Completeness=1.00 (4.4s)
- `retry.json`: Explanation Accuracy=0.90, Context Awareness=0.60, Terminology Correctness=0.95, Completeness=0.80 (5.2s)
- `reverse_words.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (5.4s)
- `safe_counter.json`: Explanation Accuracy=0.80, Context Awareness=0.20, Terminology Correctness=0.90, Completeness=0.60 (3.5s)
- `safe_counter_init.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (5.0s)
- `sorted_students.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (5.0s)
- `total_variable.json`: Explanation Accuracy=0.80, Context Awareness=0.40, Terminology Correctness=0.60, Completeness=0.40 (2.7s)
- `try_except.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (4.7s)
- `while_loop.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (5.6s)

