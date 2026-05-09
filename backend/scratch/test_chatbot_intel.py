import asyncio
import os
import sys
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

async def test_chat():
    try:
        from scraper import NeuralKnowledge
        from local_db import get_db
        
        db = await get_db('autonorth')
        inventory = await db.vehicles.find({}).to_list(100)
        
        queries = [
            "Do you have any Ford F-150?",
            "I'm looking for an SUV",
            "What's your best deal?",
            "How can I contact you?",
            "Tell me about financing"
        ]
        
        print(f"Testing Chatbot with {len(inventory)} vehicles in stock...\n")
        
        for q in queries:
            print(f"User: {q}")
            # Simulate local provider (no API key)
            response = await NeuralKnowledge.generate_response(q, inventory, provider="local", api_key="")
            print(f"AI: {response}\n")
            print("-" * 30)
            
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat())
