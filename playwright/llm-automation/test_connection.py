import asyncio
from openai import AsyncOpenAI
import os

async def test_openai_connection():
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say this is a test"}],
            max_tokens=5
        )
        print("OpenAI API connection successful!")
        print("Response:", response.choices[0].message.content)
    except Exception as e:
        print("OpenAI API connection failed!")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_openai_connection())
