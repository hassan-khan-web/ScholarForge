import os
from dotenv import load_dotenv
load_dotenv()
import AI_engine

def test_assess_search_need():
    print("--- Test 1: Well-known topic (Should SKIP) ---")
    query_1 = "The Solar System planets"
    result_1 = AI_engine.assess_search_need(query_1, "")
    print(f"Query: {query_1}")
    print(f"Result: {result_1}")
    
    print("\n--- Test 2: Current Event (Should SEARCH) ---")
    query_2 = "Latest iPhone 16 release date rumors 2025"
    result_2 = AI_engine.assess_search_need(query_2, "")
    print(f"Query: {query_2}")
    print(f"Result: {result_2}")

if __name__ == "__main__":
    test_assess_search_need()
