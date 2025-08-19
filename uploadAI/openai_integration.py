import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_openai(context, question):
    prompt = f"""
You are a helpful assistant. Use the following company data to answer the user's question.

DATA:
{context}

Question: {question}

Answer:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",  # or use "gpt-3.5-turbo" if needed
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI error: {str(e)}"
