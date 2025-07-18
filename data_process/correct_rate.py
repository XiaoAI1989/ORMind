"""Recompute the paper's metrics (SR / MFFR / IEFR) from a run directory.

Each ``*_test_log.txt`` written by the experiment runner ends with a
"Final Result: <NAME>" line; this script aggregates those lines.
"""

import argparse
import os
import re


def count_cases(folder_path):
    pattern = r'.*_test_log\.txt$'
    final_result_pattern = re.compile(r'Final Result: (\w+)')
    counts = {
        'ACCEPT': 0,
        'WRONG_ANSWER': 0,
        'MODEL_FAILURE': 0,
        'RUNTIME_ERROR': 0,
        'COMPILE_ERROR': 0,
        'UNKNOWN': 0,
    }
    total_files = 0

    for filename in os.listdir(folder_path):
        if re.match(pattern, filename):
            total_files += 1
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            match = final_result_pattern.search(content)
            if match and match.group(1) in counts:
                counts[match.group(1)] += 1
            else:
                counts['UNKNOWN'] += 1

    return total_files, counts


def main():
    parser = argparse.ArgumentParser(description="Aggregate SR/MFFR/IEFR from test logs.")
    parser.add_argument("--folder", type=str, default="../log", help="Run directory containing *_test_log.txt files")
    args = parser.parse_args()

    total, counts = count_cases(args.folder)
    if total == 0:
        print(f"No test logs found in {args.folder}")
        return

    iefr = counts['RUNTIME_ERROR'] + counts['COMPILE_ERROR']
    print(f"Total problems: {total}")
    print(f"SR   (Success Rate):                      {counts['ACCEPT']} ({counts['ACCEPT'] / total:.2%})")
    print(f"MFFR (Model Formulation Failure Rate):    {counts['MODEL_FAILURE']} ({counts['MODEL_FAILURE'] / total:.2%})")
    print(f"IEFR (Implementation Execution Failure):  {iefr} ({iefr / total:.2%})")
    print(f"WA   (Wrong Answer):                      {counts['WRONG_ANSWER']} ({counts['WRONG_ANSWER'] / total:.2%})")
    if counts['UNKNOWN']:
        print(f"Unclassified logs: {counts['UNKNOWN']}")


if __name__ == "__main__":
    main()
