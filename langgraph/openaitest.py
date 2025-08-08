import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# New OpenAI v1.x syntax
client = openai.OpenAI(api_key=openai.api_key)
models = client.models.list()

for model in models.data:
    print(model.id)