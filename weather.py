"""
weather.py

Demonstrates function/tool calling with a local Ollama model (functiongemma)
using the `ollama` Python client. Tests the model with the prompt:
"What is the weather in Paris?"

Prerequisites:
    1. Install and run Ollama locally: https://ollama.com
    2. Pull the model:      ollama pull functiongemma:latest
    3. Install the client:  pip install ollama

Run:
    python weather.py
"""

import json
import sys

from ollama import chat, ResponseError

MODEL = "functiongemma:latest"


def get_weather(city: str) -> str:
    """
    Get the current weather for a city.
    (Mocked here — swap in a real weather API call if needed.)

    Args:
        city: The name of the city

    Returns:
        A JSON string describing the weather.
    """
    # Simple mock data; replace with e.g. an OpenWeatherMap call for real results.
    fake_data = {
        "paris": {"temperature": 22, "unit": "celsius", "condition": "sunny"},
        "london": {"temperature": 17, "unit": "celsius", "condition": "cloudy"},
        "bengaluru": {"temperature": 27, "unit": "celsius", "condition": "humid"},
    }
    info = fake_data.get(city.strip().lower(), {"temperature": 20, "unit": "celsius", "condition": "unknown"})
    return json.dumps({"city": city, **info})


def run(prompt: str) -> None:
    messages = [{"role": "user", "content": prompt}]
    print(f"Prompt: {prompt}\n")

    try:
        response = chat(MODEL, messages=messages, tools=[get_weather])
    except ResponseError as e:
        print(f"Ollama error: {e}")
        print(f"Make sure the server is running and the model is pulled: `ollama pull {MODEL}`")
        sys.exit(1)
    except Exception as e:
        print(f"Could not reach local Ollama server: {e}")
        print("Start it with `ollama serve` (or ensure the Ollama app is running).")
        sys.exit(1)

    # print("Model response object:")
    # print(response.message)
    print()

    if response.message.tool_calls and response.message.tool_calls[0].function.name:
        tool_call = response.message.tool_calls[0]
        print(f"Model requested tool call: {tool_call.function.name}({tool_call.function.arguments})")

        if not tool_call.function.arguments.get("city"):
            print(
                "Tool call returned no 'city' argument. This usually means Ollama "
                "couldn't parse functiongemma's chat template — check `ollama --version` "
                "(needs >= 0.13.5) and re-pull the model."
            )
            sys.exit(1)

        result = get_weather(**tool_call.function.arguments)
        print(f"Tool result: {result}\n")

        # Feed the tool result back to the model for a final natural-language answer
        messages.append(response.message)
        messages.append({"role": "tool", "content": result})

        final = chat(MODEL, messages=messages)
        print("Final answer:")
        print(final.message.content)
    else:
        print("No valid tool call made. Raw content:", repr(response.message.content))
        print(
            "\nIf this looks garbled (e.g. stray words instead of a clean response), "
            "it's likely an Ollama-version/model-template mismatch, not a script bug. "
            "FunctionGemma requires Ollama v0.13.5+. Run `ollama --version` to check, "
            "update if older, then `ollama rm functiongemma:latest && ollama pull functiongemma:latest`."
        )


if __name__ == "__main__":
    run("What is the weather in Paris?")