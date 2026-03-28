import requests

URL = "http://localhost:11434/api/generate"

def translate(text, source_lang, target_lang):
    prompt = f"Translate from {source_lang} to {target_lang}:\n{text}"

    payload = {
        "model": "translategemma:4b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(URL, json=payload)
    return response.json()["response"]

if __name__ == "__main__":
    text = "Raman is a very good person"
    translated = translate(text, "English", "Hindi")
    print("Translated text:")
    print(translated)
