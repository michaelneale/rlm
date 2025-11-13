#!/usr/bin/env python3
"""
Test script for RLM with a smaller, more manageable example.
"""
from rlm.rlm_repl import RLM_REPL
import random

def generate_small_context(num_lines: int = 100, answer: str = "42") -> str:
    """Generate a small context for testing without huge costs."""
    print(f"Generating small context with {num_lines} lines...")
    
    # Set of random words to use
    random_words = ["hello", "world", "test", "data", "sample", "information", "content", "example"]
    
    lines = []
    for i in range(num_lines):
        if i == num_lines // 2:  # Put the answer in the middle
            lines.append(f"The magic number is {answer}")
        else:
            num_words = random.randint(3, 6)
            line_words = [random.choice(random_words) for _ in range(num_words)]
            lines.append(" ".join(line_words))
    
    print(f"Magic number '{answer}' inserted at line {num_lines // 2}")
    return "\n".join(lines)

def test_basic_rlm():
    """Test RLM with a simple needle-in-haystack problem."""
    print("Testing RLM with a small needle-in-haystack problem...")
    
    answer = "42"
    context = generate_small_context(num_lines=50, answer=answer)
    
    # Use actual OpenAI model names
    rlm = RLM_REPL(
        model="gpt-4o-mini",  # Cheaper model for main processing
        recursive_model="gpt-4o-mini",  # Same model for recursive calls
        enable_logging=True,
        max_iterations=5  # Limit iterations to control costs
    )
    
    query = "I'm looking for a magic number. What is it?"
    print(f"\nQuery: {query}")
    print(f"Expected answer: {answer}")
    print("\n" + "="*50)
    
    try:
        result = rlm.completion(context=context, query=query)
        print(f"\nFINAL RESULT: {result}")
        print(f"Expected: {answer}")
        
        # Check if the result contains the expected answer
        if answer in str(result):
            print("✅ SUCCESS: Found the magic number!")
        else:
            print("❌ The magic number was not found in the result.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_basic_rlm()
