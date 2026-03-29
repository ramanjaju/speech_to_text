import requests

class GemmaTranslator:
    def __init__(self, api_url: str = "http://localhost:11434/api/generate", model_name: str = "gemma2:2b"):
        self.api_url = api_url
        self.model_name = model_name

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        prompt = f"Translate from {source_lang} to {target_lang}:\n{text}"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json()["response"].strip()
        except Exception as e:
            print(f"Error during translation request: {e}")
            return f"Translation error: {e}"

if __name__ == "__main__":
    translator = GemmaTranslator()
    text_to_translate = "Hello, how are you?"
    translated_text = translator.translate(text_to_translate, "English", "Hindi")
    print(f"Original text: {text_to_translate}")
    print(f"Translated text: {translated_text}")
