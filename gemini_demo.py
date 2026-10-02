import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash-lite"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

def ask_gemini(prompt: str) -> dict:
    headers = {"x-goog-api-key": API_KEY}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()

def extract_text(data: dict) -> str:
    return data["candidates"][0]["content"]["parts"][0]["text"]

def main() -> None:
    if not API_KEY:
        print("GEMINI_API_KEY non trovata: controlla il file .env")
        return
    
    prompt = "Traduci in giapponese: 'Dove è la stazione?'. Dammi anche il romaji"
    data = {}
    try:
        data = ask_gemini(prompt)
        print(extract_text(data))
        print("Token:", data.get("usageMetadata"))
    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP {e.response.status_code}: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Errore di rete: {e}")
    except (KeyError, IndexError):
        print("Risposta in un formato inatteso:")
        print(data)
        
if __name__ == "__main__":
    main()
        