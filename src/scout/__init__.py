"""Scout module entry point."""
import os
from dotenv import load_dotenv
from ollama import Client

load_dotenv()

api_key = os.environ.get("OLLAMA_API_KEY", "")
headers = {"Authorization": f"Bearer {api_key}"}

client = Client(
    host="https://ollama.com",
    headers=headers
)

messages = [
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
]

for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
    print(part['message']['content'], end='', flush=True)