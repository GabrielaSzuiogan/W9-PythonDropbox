import voyageai
from config.settings import settings

# Initialize the client once here
voyage_client = voyageai.Client(api_key=settings.voyage_api_key)

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Splits a long string of text into overlapping chunks."""
    chunks = []
    start_idx = 0
    while start_idx < len(text):
        end_idx = min(start_idx + chunk_size, len(text))
        chunks.append(text[start_idx:end_idx])
        start_idx = end_idx - chunk_overlap if end_idx < len(text) else len(text)
    return chunks

def get_embeddings(chunks: list[str]) -> list[list[float]]:
    """Sends a list of text chunks to Voyage AI and returns their vector embeddings."""
    if not chunks:
        return []
    
    # We use voyage-4 with 2048 dimensions to match our Postgres database column
    response = voyage_client.embed(
        chunks, 
        model="voyage-4", 
        output_dimension=2048
    )
    return response.embeddings