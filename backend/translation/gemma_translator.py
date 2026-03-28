import requests
from src.core.config import Config

class GemmaTranslator:
    def __init__(self):
        config = Config()
        self.api_url = config.get('ollama.api_url')
        self.model_name = config.get('ollama.model_name')

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        prompt = f"Translate from {source_lang} to {target_lang}:\n{text}"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            print(f"Error during translation request: {e}")
            return f"Translation error: {e}"

if __name__ == "__main__":
    # Example usage:
    # Note: For this example to work, config.yaml must be set up correctly
    # and the Ollama server must be running.
    config = Config()
    source_lang = config.get('app.source_language', 'English')
    target_lang = config.get('app.target_language', 'Hindi')

    translator = GemmaTranslator()
    text_to_translate = "Raman is a very good person"
    translated_text = translator.translate(text_to_translate, source_lang, target_lang)
    print(f"Original text: {text_to_translate}")
    print(f"Translated text: {translated_text}")
