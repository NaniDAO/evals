import json
import os
from collections import defaultdict
from rich import print
from rich.console import Console

console = Console()


def get_json_files(directory):
    return [f for f in os.listdir(directory) if f.endswith(".json")]


def load_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def count_refusal_sentiments(data):
    sentiment_counts = defaultdict(list)
    explanations = defaultdict(list)
    if "layer_candidates" in data:
        for candidate in data["layer_candidates"]:
            sentiment = candidate["refusal_sentiment"]
            number = candidate["number"]
            explanation = candidate["explanation"]
            sentiment_counts[sentiment].append(number)
            explanations[sentiment].append((number, explanation))
    return sentiment_counts, explanations


def main():
    directory = "./out"
    json_files = get_json_files(directory)

    for json_file in json_files:
        file_path = os.path.join(directory, json_file)
        data = load_json(file_path)
        sentiment_counts, explanations = count_refusal_sentiments(data)

        if sentiment_counts:
            console.print("\n" + "=" * 40, style="cyan")
            console.print(f"File: {json_file}", style="cyan")
            console.print("=" * 40, style="cyan")
            for sentiment, numbers in sentiment_counts.items():
                console.print(f"\n{sentiment.capitalize()}:", style="yellow")
                console.print(
                    f"  Completion Numbers: {', '.join(map(str, numbers))}",
                    style="green",
                )
                console.print(f"  Unique Explanations:", style="magenta")
                for number, explanation in explanations[sentiment]:
                    console.print(f"    - {number}: {explanation}", style="white")


if __name__ == "__main__":
    main()
