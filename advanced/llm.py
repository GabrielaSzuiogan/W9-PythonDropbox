from groq import Groq
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])


# --- weather
def get_weather(city: str) -> str:
  """Get the weather of a city"""
  return "22 degrees Celsius"

weather_schema = {
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "Get the weather of a city",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "Name of the city"
        }
      },
      "required": ["city"]
    }
  }
}


# --- age check

def get_person_age(name: str) -> str:
    """Get the age of a specific person"""
    mock_db = {
        "gabi": "23",
        "maria": "30",
        "sarah": "20"
    }
    age = mock_db.get(name.lower(), "I dont know that person!")
    return f"{age} years old"

age_schema = {
  "type": "function",
  "function": {
    "name": "get_person_age",
    "description": "Get the age of a specific person by their name",
    "parameters": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "The first name of the person, e.g., Gabi"
        }
      },
      "required": ["name"]
    }
  }
}


# -- read file
def read_file(file_path: str) -> str:
    """Read the contents of a text file from the local computer"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content
    except FileNotFoundError:
        return f"Error: Could not find a file named '{file_path}'."
    except Exception as e:
        return f"Error reading the file: {e}"

read_file_schema = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a local file. Use this when the user asks you to summarize, read, or extract info from a specific file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string", 
                    "description": "The name or path of the file to read, e.g., 'sample.txt' or 'config/settings.py'"
                }
            },
            "required": ["file_path"]
        }
    }
}

# --- logic
available_functions = {
    "get_weather": get_weather,
    "get_person_age": get_person_age,
    "read_file": read_file,
}

def execute_tool_call(tool_call):
    """Parse and execute a single tool call"""
    function_name = tool_call.function.name
    function_to_call = available_functions[function_name]
    function_args = json.loads(tool_call.function.arguments)
    
    return function_to_call(**function_args)


# --- chat setup
class TeacherInfo(BaseModel):
  name: str
  age: int

system_prompt = """
You are a helpful tutor for a programming language called Python.
CRITICAL INSTRUCTIONS:
If the user asks you to read a file, you must use the 'read_file' tool.
"""

messages = [
    {
        "role": "system",
        "content": system_prompt
    }
]

def add_message( text: str):
  messages.append({"role": "user", "content": text})

def add_ai_message(text: str):
  messages.append({"role": "assistant", "content": text})

def run_completion(messages):
  completion = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=messages,
    tools=[weather_schema, age_schema, read_file_schema],
    tool_choice="auto",
  )

  return completion.choices[0].message

# # --- run
# add_message("\nWhat is the weather in Bucharest?\n")
# response = run_completion(messages)

# if response.tool_calls:

#   messages.append(response.model_dump(exclude_unset=True))
#   for tool_call in response.tool_calls:
#     print(f"-> AI is calling tool: {tool_call.function.name}")
#     tool_result = execute_tool_call(tool_call)
    
#     messages.append({
#       "role": "tool",
#       "tool_call_id": tool_call.id,
#       "name": tool_call.function.name,
#       "content": str(tool_result)
#     })

#   response = run_completion(messages)
#   add_ai_message(response.content)
#   print(response.content)

#   print("\nIn background:")
#   for message in messages:
#     print(message)



print("\n" + "="*60)
print(" Chat with AI: (Type 'exit' to quit)")
print("="*60)

while True:
  try:
      # users input
      user_input = input("\nYou: ")
      if user_input.lower() in ['exit', 'quit', 'bye']:
          break
      if not user_input.strip():
          continue

      add_message(user_input)

      # send to AI
      response = run_completion(messages)

      # check if it using the tool
      if response.tool_calls:
          # save the AI's tool request
          messages.append(response.model_dump(exclude_unset=True))
            
          # execute requested tools
          for tool_call in response.tool_calls:
              print(f"  [ Executing Tool: {tool_call.function.name}...]")
              tool_result = execute_tool_call(tool_call)
                
              # save the tool results
              messages.append({
                  "role": "tool",
                  "tool_call_id": tool_call.id,
                  "name": tool_call.function.name,
                  "content": str(tool_result)
              })

          response = run_completion(messages)

      # extract the final text response
      final_text = response.content
      add_ai_message(final_text)

      # response
      print("-" * 80)
      print(f" AI: {final_text}")
      print("-" * 80)

  except (EOFError, KeyboardInterrupt):
      print("\nGoodbye!")
      break
  except Exception as e:
      print(f"\nAn error occurred: {e}")
      break
