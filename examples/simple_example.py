#!/usr/bin/env python3
"""
Simple example: Query a small text file using RLM via OpenAI API.
"""

from openai import OpenAI

# Connect to RLM server
client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

# Small test document
small_doc = """
Python Programming Guide

Chapter 1: Variables
Variables store data. Use = to assign values.
Example: x = 5

Chapter 2: Functions  
Functions are reusable code blocks.
Example: def greet(): print("Hello")

Chapter 3: Lists
Lists store multiple items.
Example: nums = [1, 2, 3]

This guide has 3 chapters total.
"""

print("📄 Simple Example: Small Document Query\n")

response = client.chat.completions.create(
    model="rlm-gpt-4o-mini",
    messages=[
        {"role": "system", "content": small_doc},
        {"role": "user", "content": "How many chapters are in this guide?"}
    ]
)

print(f"💡 Answer: {response.choices[0].message.content}\n")
