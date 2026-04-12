import requests
import json

class GemmaTranslator:
    def __init__(self, api_url: str = "http://localhost:11434/api/generate", model_name: str = "gemma2:2b"):
        self.api_url = api_url
        self.model_name = model_name

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        prompt = f"Translate the following text from {source_lang} to {target_lang}. Output ONLY the translation and nothing else. No explanations, no notes:\n\n{text}"
        return self._generate(prompt, "You are a professional translator. Output only raw translated text.")

    def chat(self, text: str) -> str:
        """
        Processes vocal input as a chat prompt and returns a concise response.
        """
        return self._generate(text, "You are a helpful AI assistant. The user is talking to you via voice. Keep your responses very brief (1-2 sentences) and conversational.")

    def _generate(self, prompt: str, system_instruction: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_ctx": 1024,
                "num_predict": 150
            }
        }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json()["response"].strip()
        except Exception as e:
            print(f"Error during LLM request: {e}")
            return f"Error: {e}"

    def stream_translate(self, text: str, source_lang: str, target_lang: str):
        """
        Yields chunks of the translation for real-time streaming.
        """
        prompt = f"Translate from {source_lang} to {target_lang}:\n{text}"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True
        }

        try:
            with requests.post(self.api_url, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        if not chunk.get("done"):
                            yield chunk.get("response", "")
        except Exception as e:
            yield f" [Error: {e}] "

if __name__ == "__main__":
    translator = GemmaTranslator()
    text_to_translate = "Hello, how are you?"
    translated_text = translator.translate(text_to_translate, "English", "Hindi")
    print(f"Original text: {text_to_translate}")
    print(f"Translated text: {translated_text}")
