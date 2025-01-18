import json
from typing import Dict, List, Set
from collections import defaultdict

def transform_json(input_file: str, output_file: str) -> None:
    # Read the input JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create a dictionary to store unique values for each feature
    unique_values: Dict[str, Set[str]] = defaultdict(set)
    
    # Extract unique values from each row
    for row_data in data['rows']:
        row = row_data['row']
        for feature in data['features']:
            feature_name = feature['name']
            # Skip Index feature since it's just a counter
            if feature_name != 'Index':
                value = row[feature_name]
                unique_values[feature_name].add(value)
    
    # Convert sets to sorted lists for JSON serialization
    unique_features = {
        key: sorted(list(values))
        for key, values in unique_values.items()
    }
    
    # Add the unique values to the original data structure
    data['unique_features'] = unique_features
    
    # Write the transformed data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    input_file = "JBB_dataset.json"  # Replace with your input file name
    output_file = "transformed.json"  # Replace with desired output file name
    
    try:
        transform_json(input_file, output_file)
        print(f"Successfully transformed JSON file. Output saved to {output_file}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()