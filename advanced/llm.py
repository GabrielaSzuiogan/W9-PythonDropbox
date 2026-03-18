from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

chunk1 = """
You are a helpful tutor for a programming language called Python.

You know about Alexandru Ghiura who is the teacher of the course, has 20y and is veryyyyyy smart
"""

def search_info(query: str):
  return chunk1

messages = [
    {
        "role": "system",
        "content": chunk1
    }
]


def add_message( text: str):
  messages.append({"role": "user", "content": text})

def add_ai_message(text: str):
  messages.append({"role": "assistant", "content": text})

def run_completion(messages):
  completion = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=messages,
  )

  return completion.choices[0].message.content

# print(completion.choices[0].message.content)

while True:
  try:
    # 1. add user message
    user_input = input("> ")
    add_message(user_input)

    # 2. run messages and add ai meesage
    response = run_completion(messages)
    add_ai_message(response)
    
    print(messages)

    # 3. print response
    print("-" * 100)
    print(response)
    print("-" * 100)
    print("\n")

  except (EOFError, KeyboardInterrupt):
    # Handles cell interruption or graceful stop
    #print(messages)
    break
  except Exception as e:
    # Catch other unexpected errors
    print(f"An error occurred: {e}")
    break