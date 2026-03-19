import sys
import os

# 1. Tell Python where to find your project folders so imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from groq import Groq
from config.settings import settings
from db.database import Session 
from api.services.file_service import FileService

# Initialize clients
client = Groq(api_key=settings.groq_api_key)
file_service = FileService()

# Since this is a terminal script, we hardcode the user ID.
# Change '1' to the actual ID of the user whose files you want to search!
TEST_USER_ID = 1 

def search_info(query: str) -> str:
    """Searches the database for chunks matching the user's query and combines them."""
    db = Session()
    try:
        # Ask your file service to do the vector search
        results = file_service.search_content(
            query=query, 
            user_id=TEST_USER_ID, 
            db=db, 
            limit=3 # Grab the top 3 most relevant chunks
        )
        
        if not results:
            return "No relevant information found in the database."

        # Extract the text_content from the chunks and combine them into one big string
        context_texts = []
        for res in results:
            chunk_text = res["chunk"]["text_content"]
            context_texts.append(f"- {chunk_text}")
            
        return "\n".join(context_texts)
    finally:
        db.close() # Always close the DB connection when done!

# We start with a base system message to tell the AI how to behave
messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant. You will be provided with context from the user's files. Answer their questions based ONLY on that context. If the answer is not in the context, say 'I don't know based on your files.'"
    }
]

def add_message(text: str):
    messages.append({"role": "user", "content": text})

def add_ai_message(text: str):
    messages.append({"role": "assistant", "content": text})

def run_completion(current_messages):
    completion = client.chat.completions.create(
        model="llama3-8b-8192", # Using a fast, valid Groq model
        messages=current_messages,
    )
    return completion.choices[0].message.content

def main():
    print("\n" + "="*60)
    print("🤖 AI File Assistant Started! (Type 'exit' or 'quit' to stop)")
    print("="*60)
    
    while True:
        try:
            # 1. Get user input
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            if not user_input.strip():
                continue

            # 2. Search the database for relevant chunks using their input!
            print("🔍 Searching your files for context...")
            db_context = search_info(user_input)
            
            # 3. Create a temporary message combining their question AND the database context
            augmented_prompt = f"Context from database:\n{db_context}\n\nUser Question: {user_input}"
            
            # Add the augmented prompt to the chat history
            add_message(augmented_prompt)

            # 4. Send to Groq and get the response
            response = run_completion(messages)
            add_ai_message(response)
            
            # 5. Print the AI's response
            print("\n" + "-" * 80)
            print(f"🤖 AI: {response}")
            print("-" * 80)

        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            break

if __name__ == "__main__":
    main()