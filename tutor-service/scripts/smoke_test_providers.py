
import asyncio
import sys
from pathlib import Path

# Add the project root (one level up from scripts/) to Python's search path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from llm.provider import get_provider


async def test_provider(name: str):
    print(f"\n--- {name} ---")
    try:
        provider = get_provider(name)
        response = await provider.complete(
            system="You are a helpful assistant. Keep replies short.",
            messages=[{"role": "user", "content": "Say hi in one sentence."}],
        )
        print("Reply:", response.text)
        print("Stop reason:", response.stop_reason)
    except Exception as e:
        print("FAILED:", repr(e))


async def main():
    for name in ["gemini", "deepseek"]:
        await test_provider(name)


asyncio.run(main())