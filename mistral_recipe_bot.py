
import requests

def get_mistral_recipes(prompt, mistral_api_key="1I0BiIiBuxpv8xXlposfEkrzx93rsZWO"):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {mistral_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-medium",
        "messages": [
            {
                "role": "system",
                "content": "You are a recipe expert. Provide simple, budget-friendly recipes using ingredients from the user's shopping list or preferences."
            },
            {
                "role": "user",
                "content": f"Give me some easy recipes using items related to: {prompt}"
            }
        ],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content']
