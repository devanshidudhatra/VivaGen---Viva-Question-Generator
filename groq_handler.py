import os
from groq import Groq

def initialize_groq():
    """Initialize the Groq client."""
    api_key = "GROQ_API_KEY"
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not set.")
        return None
    try:
        client = Groq(api_key=api_key)
        return client
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return None

def generate_evaluation_questions(content):
    """Generate evaluation questions using the Groq API."""
    client = initialize_groq()
    if client is None:
        return []

    model_name = "meta-llama/llama-4-maverick-17b-128e-instruct"  # Or another suitable model
    prompt = f"""
    Generate 5 critical evaluation questions based on this assignment content:
    {content[:3000]}  # Limiting input size

    Requirements:
    1. Focus on core concepts
    2. Include both theoretical and practical aspects
    3. Ensure questions require analytical thinking
    4. Format as numbered list
    5. Avoid yes/no questions
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_name,
            temperature=0.7,
            max_tokens=1024,
        )
        # Extract and format questions from the response
        response_text = chat_completion.choices[0].message.content
        questions = [q.split('. ', 1)[1] for q in response_text.split('\n') if q.strip() and '. ' in q]
        return questions
    except Exception as e:
        print(f"Error generating evaluation questions with Groq: {e}")
        return []
