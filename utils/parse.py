import json

def parse_prompt_md(file_path):
    """
    Parse the prompt.md file and return structured JSON data.
    
    Args:
        file_path (str): Path to the prompt.md file
        
    Returns:
        dict: Structured data containing instructions and completions
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Initialize the data structure
        data = {
            "instructions": []
        }
        
        # Split content by instructions
        parts = content.split('INSTRUCTION ')
        
        # Process each instruction section (skip first empty part)
        for part in parts[1:]:  # Skip the first split which is empty or contains header
            if not part.strip():
                continue
                
            # Extract instruction number and text
            instruction_lines = part.split('\n', 1)[0]  # Get first line with instruction
            instruction_text = instruction_lines.split("'")[1] if "'" in instruction_lines else ""
            
            instruction_data = {
                "instruction": instruction_text,
                "baseline_completion": "",
                "layer_candidates": []
            }
            
            # Find baseline completion
            if 'BASELINE COMPLETION:' in part:
                baseline_section = part.split('BASELINE COMPLETION:', 1)[1]
                baseline_text = baseline_section.split('LAYER CANDIDATE')[0] if 'LAYER CANDIDATE' in baseline_section else baseline_section
                # Clean up the baseline text
                baseline_text = baseline_text.strip().strip('"').strip("'")
                instruction_data["baseline_completion"] = baseline_text
            
            # Find all layer candidates
            lines = part.split('\n')
            current_candidate = None
            candidate_text = []
            
            for line in lines:
                if line.strip().startswith('LAYER CANDIDATE #'):
                    # If we were collecting a previous candidate, save it
                    if current_candidate is not None and candidate_text:
                        candidate_completion = '\n'.join(candidate_text).strip().strip('"').strip("'")
                        instruction_data["layer_candidates"].append({
                            "number": current_candidate,
                            "completion": candidate_completion
                        })
                        candidate_text = []
                    
                    # Start new candidate
                    current_candidate = int(line.split('#')[1].split()[0])
                elif 'INTERVENTION COMPLETION:' in line:
                    continue
                elif current_candidate is not None:
                    candidate_text.append(line.strip())
            
            # Add the last candidate if exists
            if current_candidate is not None and candidate_text:
                candidate_completion = '\n'.join(candidate_text).strip().strip('"').strip("'")
                instruction_data["layer_candidates"].append({
                    "number": current_candidate,
                    "completion": candidate_completion
                })
            
            data["instructions"].append(instruction_data)
        
        return data
    
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except Exception as e:
        print(f"Error parsing file: {str(e)}")
        return None

def save_json(data, output_file):
    """
    Save the structured data as a JSON file.
    
    Args:
        data (dict): The structured data to save
        output_file (str): The path where to save the JSON file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    # Parse the prompt.md file
    data = parse_prompt_md('data/prompts_eval.md')
    
    if data:
        # Save to JSON file
        save_json(data, 'data/output.json')
        # Print the result
        print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()