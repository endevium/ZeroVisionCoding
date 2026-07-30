# AI Accuracy Report (LLM-as-a-Judge)

Evaluated using Groq for subjective metrics.

## Code Debugging (Fixer)
- **Error Detection Accuracy:** 54.2%
- **Fix Success Rate:** 100.0%
- **Runtime Success Rate:** 83.3%
- **Logic Preservation Rate:** 45.8%
- **Average Response Time:** 10.43s

### Log
- `assertion_error.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (17.3s)
- `attribute_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (8.1s)
- `call_none.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (9.4s)
- `empty_pop.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (10.5s)
- `file_not_found.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=1.00 (14.5s)
- `float_division_zero.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (9.3s)
- `indentation_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (10.1s)
- `index_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (9.3s)
- `int_subscript.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (11.2s)
- `key_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (9.1s)
- `list_index_negative.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=0.00 (10.5s)
- `module_not_found.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=0.00 (8.9s)
- `name_error.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (9.4s)
- `nested_key_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (8.5s)
- `none_append.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (9.0s)
- `recursion_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (10.9s)
- `syntax_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (6.1s)
- `type_error_args.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (9.6s)
- `type_error_concat.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=0.00, Logic Preservation Rate=0.00 (11.0s)
- `unbound_local.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (14.4s)
- `unpack_error.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (12.3s)
- `value_error.json`: Error Detection Accuracy=0.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (10.1s)
- `wrong_function_usage.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=1.00 (10.5s)
- `zero_division.json`: Error Detection Accuracy=1.00, Fix Success Rate=1.00, Runtime Success Rate=1.00, Logic Preservation Rate=0.00 (10.1s)

## Code Review
- **Issue Detection Accuracy:** 7.0%
- **False Positive Rate:** 10.5%
- **Suggestion Quality:** 13.2%
- **Severity Classification Accuracy:** 5.3%
- **Average Response Time:** 21.02s

### Log
- `bare_except.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (32.6s)
- `broad_exception.json`: Issue Detection Accuracy=0.00, False Positive Rate=1.00, Suggestion Quality=0.50, Severity Classification Accuracy=0.00 (16.3s)
- `clean_code.json`: Issue Detection Accuracy=1.00, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=1.00 (10.2s)
- `comparison_is_string.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (15.1s)
- `debug_prints.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (14.5s)
- `division_no_check.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (12.1s)
- `global_mutation.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (24.0s)
- `infinite_loop.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (91.5s)
- `list_concat_loop.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (18.8s)
- `magic_number.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (17.5s)
- `missing_return.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (13.6s)
- `missing_validation.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (9.8s)
- `mutable_default.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (26.0s)
- `no_docs.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (11.4s)
- `off_by_one.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (13.2s)
- `recursion_no_base.json`: Issue Detection Accuracy=0.33, False Positive Rate=0.00, Suggestion Quality=1.00, Severity Classification Accuracy=0.00 (17.1s)
- `shadow_builtin.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (14.4s)
- `unreachable_return.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (14.5s)
- `unused_variable.json`: Issue Detection Accuracy=0.00, False Positive Rate=0.00, Suggestion Quality=0.00, Severity Classification Accuracy=0.00 (26.6s)

## Analyze Code
- **Analysis Accuracy:** 91.6%
- **Logic Explanation Accuracy:** 95.6%
- **Issue Detection Rate:** 0.0%
- **Suggestion Relevance:** 0.0%
- **Average Response Time:** 14.51s

### Log
- `anagram_check.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (18.8s)
- `average_grade.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (10.8s)
- `binary_search.json`: Analysis Accuracy=0.80, Logic Explanation Accuracy=0.90, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (22.7s)
- `bubble_sort.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (11.6s)
- `calculator.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (15.7s)
- `celsius_to_fahrenheit.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.90, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (9.9s)
- `class_student.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (15.5s)
- `factorial_iterative.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (12.2s)
- `fibonacci.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (18.3s)
- `file_counter.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (14.4s)
- `find_largest.json`: Analysis Accuracy=1.00, Logic Explanation Accuracy=1.00, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (13.5s)
- `fizzbuzz.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (16.9s)
- `json_parse.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (9.0s)
- `linear_search.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (12.5s)
- `list_comprehension.json`: Analysis Accuracy=1.00, Logic Explanation Accuracy=1.00, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (10.7s)
- `matrix_transpose.json`: Analysis Accuracy=1.00, Logic Explanation Accuracy=1.00, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (13.0s)
- `merge_dicts.json`: Analysis Accuracy=1.00, Logic Explanation Accuracy=1.00, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (8.6s)
- `palindrome_check.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (9.5s)
- `prime_check.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (10.8s)
- `read_csv.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (27.4s)
- `remove_duplicates.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (16.2s)
- `running_average.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (16.5s)
- `stack_implementation.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (20.4s)
- `sum_digits.json`: Analysis Accuracy=0.90, Logic Explanation Accuracy=0.95, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (14.1s)
- `word_frequency.json`: Analysis Accuracy=1.00, Logic Explanation Accuracy=1.00, Issue Detection Rate=0.00, Suggestion Relevance=0.00 (13.6s)

## Explain Code
- **Explanation Accuracy:** 92.1%
- **Context Awareness:** 61.7%
- **Terminology Correctness:** 92.9%
- **Completeness:** 77.1%
- **Average Response Time:** 4.71s

### Log
- `class_animal.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (7.3s)
- `class_method.json`: Explanation Accuracy=0.90, Context Awareness=0.60, Terminology Correctness=0.90, Completeness=0.70 (2.6s)
- `context_manager.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (4.5s)
- `count_vowels.json`: Explanation Accuracy=1.00, Context Awareness=0.00, Terminology Correctness=1.00, Completeness=1.00 (5.2s)
- `decimal_format.json`: Explanation Accuracy=1.00, Context Awareness=0.00, Terminology Correctness=1.00, Completeness=0.00 (1.9s)
- `decorator.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (6.7s)
- `dict_comprehension.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (3.9s)
- `filter_even.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (5.5s)
- `for_loop_sum.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (6.7s)
- `generator.json`: Explanation Accuracy=0.80, Context Awareness=0.40, Terminology Correctness=0.90, Completeness=0.70 (7.6s)
- `get_age.json`: Explanation Accuracy=1.00, Context Awareness=0.50, Terminology Correctness=1.00, Completeness=0.80 (3.6s)
- `lambda_sort.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (6.2s)
- `list_comprehension.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (3.5s)
- `main_function.json`: Explanation Accuracy=0.80, Context Awareness=0.60, Terminology Correctness=0.90, Completeness=0.70 (3.6s)
- `map_lambda.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (3.1s)
- `normalize_name.json`: Explanation Accuracy=1.00, Context Awareness=0.50, Terminology Correctness=1.00, Completeness=1.00 (4.7s)
- `retry.json`: Explanation Accuracy=0.90, Context Awareness=0.60, Terminology Correctness=0.90, Completeness=0.80 (5.2s)
- `reverse_words.json`: Explanation Accuracy=0.90, Context Awareness=0.60, Terminology Correctness=0.90, Completeness=0.80 (5.9s)
- `safe_counter.json`: Explanation Accuracy=0.80, Context Awareness=0.20, Terminology Correctness=0.90, Completeness=0.60 (3.6s)
- `safe_counter_init.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (5.3s)
- `sorted_students.json`: Explanation Accuracy=1.00, Context Awareness=0.80, Terminology Correctness=1.00, Completeness=0.90 (4.7s)
- `total_variable.json`: Explanation Accuracy=0.80, Context Awareness=0.40, Terminology Correctness=0.70, Completeness=0.50 (2.2s)
- `try_except.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (4.6s)
- `while_loop.json`: Explanation Accuracy=0.90, Context Awareness=0.80, Terminology Correctness=0.90, Completeness=0.80 (5.0s)

