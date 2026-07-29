import os
from dotenv import load_dotenv

load_dotenv()

# Add this temporary debug print
print(f"My Groq Key starts with: {str(os.getenv('GROQ_API_KEY'))}")