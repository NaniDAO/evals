import json
import os
from apis.analyzer import create_handler


def get_json_content(file_path):
    with open(file_path, "r") as file:
        return file.read()


def save_response(file_path, response):
    with open(file_path, "w") as file:
        json.dump(response, file, indent=4)


def test_gemini_all_settings_json(
    gemini_provider, gemini_api_key, gemini_model, system_prompt, prompt, config
):
    handler = create_handler(
        provider=gemini_provider,
        api_key=gemini_api_key,
        model=gemini_model,
        system_prompt=system_prompt,
        config=config,
    )
    gemini_response = handler.generate_json_response(prompt)
    save_response("gemini_response.json", gemini_response)
    print(json.dumps(gemini_response, indent=4))


def test_anthropic_all_settings_json(
    anthropic_provider,
    anthropic_api_key,
    anthropic_model,
    system_prompt,
    prompt,
    config,
):
    handler = create_handler(
        provider=anthropic_provider,
        api_key=anthropic_api_key,
        model=anthropic_model,
        system_prompt=system_prompt,
        config=config,
    )
    anthropic_response = handler.generate_json_response(prompt)
    save_response("anthropic_response.json", anthropic_response)
    print(json.dumps(anthropic_response, indent=4))


def test_gemini_default_settings(gemini_provider, gemini_api_key, prompt):
    handler = create_handler(provider=gemini_provider, api_key=gemini_api_key)
    gemini_response = handler.generate_json_response(prompt)
    save_response("gemini_response.json", gemini_response)
    print(json.dumps(gemini_response, indent=4))


def test_gemini_non_json_response(gemini_provider, gemini_api_key, prompt):
    handler = create_handler(provider=gemini_provider, api_key=gemini_api_key)
    gemini_response = handler.generate_response(prompt)
    print(gemini_response)



def main():
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    gemini_provider = "gemini"
    anthropic_provider = "anthropic"
    gemini_model = "gemini-1.5-pro-001"
    anthropic_model = "claude-3-5-sonnet-20241022"

    json_content = get_json_content("data/schema.json")

    example_config_gemini = {
        "temperature": 0.7,
        "top_p": 1.0,
        "top_k": 40,
        "candidate_count": 1,
    }

    example_config_anthropic = {
        "max_tokens": 8096,
        "temperature": 0.7,
        "top_p": 1.0,
    }

    example_system_prompt = (
        "Return only valid JSON without any explanatory text or markdown formatting"
    )

    example_prompt = f"""
    Extend this JSON schema with a new field called 'address' that is a string.

    {json_content}
    """

    test_gemini_default_settings(gemini_provider, gemini_api_key, example_prompt)

    test_gemini_all_settings_json(
        gemini_provider,
        gemini_api_key,
        gemini_model,
        example_system_prompt,
        example_prompt,
        example_config_gemini,
    )

    test_anthropic_all_settings_json(
        anthropic_provider,
        anthropic_api_key,
        anthropic_model,
        example_system_prompt,
        example_prompt,
        example_config_anthropic,
    )


if __name__ == "__main__":
    main()
