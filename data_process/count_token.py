"""Aggregate per-problem prompt-token usage from a run directory.

Each ``*_test_log.txt`` written by the experiment runner contains a
"Prompt Tokens: N" line covering the full problem run; this script
reports the mean and standard deviation (the statistics of Table 4).
"""

import argparse
import os
import re
import statistics


def count_token(folder_path):
    pattern = r'.*_test_log\.txt$'
    prompt_tokens = []
    total_files = 0

    for filename in os.listdir(folder_path):
        if re.match(pattern, filename):
            total_files += 1
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                match = re.search(r'Prompt Tokens: (\d+)', content)
                if match:
                    tokens = int(match.group(1))
                    prompt_tokens.append(tokens)

    if not prompt_tokens:
        return None

    return {
        'average': statistics.mean(prompt_tokens),
        'std_dev': statistics.stdev(prompt_tokens) if len(prompt_tokens) > 1 else 0.0,
        'total_files': total_files,
    }


def main():
    parser = argparse.ArgumentParser(description="Aggregate prompt-token statistics from test logs.")
    parser.add_argument("--folder", type=str, default="../log", help="Run directory containing *_test_log.txt files")
    args = parser.parse_args()

    result = count_token(args.folder)
    if result:
        print(f"Average Prompt Tokens: {result['average']:.2f}")
        print(f"Standard Deviation: +/-{result['std_dev']:.2f}")
        print(f"Total files processed: {result['total_files']}")
    else:
        print("No matching files found or no token information available.")


if __name__ == "__main__":
    main()
