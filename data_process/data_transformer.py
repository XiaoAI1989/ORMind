"""One-off preprocessing script (provenance tool, not part of the pipeline).

Converts Chain-of-Experts ``seeds_model`` JSON files into the
``input_targets.json`` format consumed by ``utils.read_OR_problem``. The
shipped ``dataset/ComplexOR`` was produced with this transformation; the
script is kept so the conversion is auditable. Running it requires the
upstream seeds, which are NOT distributed with this repository (see the
Chain-of-Experts release: https://github.com/xzymustbexzy/Chain-of-Experts).
"""

import argparse
import json
import os


def process_json(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as file:
        original_data = json.load(file)

    new_data = {
        "background": original_data.get("description", ""),
        "constraints": [
            constraint["description"] for constraint in original_data.get("model", {}).get("constraint", [])
        ],
        "objective": original_data.get("model", {}).get("objective", [{}])[0].get("description", ""),
        "description": original_data.get("description", ""),
        "parameters": []
    }

    for set_item in original_data.get("model", {}).get("set", []):
        new_data["parameters"].append({
            "symbol": set_item.get("name", ""),
            "definition": set_item.get("description", ""),
            "shape": []
        })

    for param in original_data.get("model", {}).get("parameter", []):
        shape = []
        domain = param.get("domain", "")
        if "," in domain:
            shape = domain.replace("{", "").replace("}", "").split(",")
            shape = [item.split("<in>")[1].strip() if "<in>" in item else item.strip() for item in shape]
        new_data["parameters"].append({
            "symbol": param.get("name", ""),
            "definition": param.get("description", ""),
            "shape": shape
        })

    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(new_data, file, indent=4, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Convert Chain-of-Experts seeds_model JSON into input_targets.json.")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory containing the upstream seeds_model *.json files")
    parser.add_argument("--output_dir", type=str, required=True, help="Dataset directory whose per-problem folders receive input_targets.json")
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        parser.error(f"--input_dir does not exist: {args.input_dir}")
    if not os.path.isdir(args.output_dir):
        parser.error(f"--output_dir does not exist: {args.output_dir}")

    existing_folders = set(os.listdir(args.output_dir))

    for filename in sorted(os.listdir(args.input_dir)):
        if filename.endswith('.json'):
            base_name = os.path.splitext(filename)[0]
            folder_name = base_name.split('_')[0]

            if folder_name not in existing_folders:
                print(f"Skipping {filename} as folder {folder_name} does not exist.")
                continue

            input_path = os.path.join(args.input_dir, filename)
            output_path = os.path.join(args.output_dir, folder_name, "input_targets.json")

            try:
                process_json(input_path, output_path)
                print(f"Processed {filename} and saved to {output_path}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
    print("All files processed.")


if __name__ == "__main__":
    main()
