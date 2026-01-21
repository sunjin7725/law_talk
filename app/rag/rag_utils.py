from openai import OpenAI

from utils import load_secret_yaml

secret = load_secret_yaml()
client = OpenAI(api_key=secret["openai"]["api_key"])

def embed_text(text):
    return client.embeddings.create(input=[text], model="text-embedding-3-large").data[0].embedding

def embed_texts(texts, batch_size=100):
    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(input=batch, model="text-embedding-3-large")
        embeddings.extend([item.embedding for item in response.data])
    return embeddings