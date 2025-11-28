import os
import ollama

# --- The old Mock AI for fallback ---
def get_mock_ai_response(query: str):
    """
    A simple rule-based AI agent that acts as a fallback.
    """
    query = query.lower()
    response = ""
    status = "closed"
    
    if "leave" in query:
        response = "Our company offers 20 days of paid leave per year. (Mock AI Response)"
    elif "password" in query and "reset" in query:
        response = "To reset your password, go to the login page and click 'Forgot Password'. (Mock AI Response)"
    elif "urgent" in query or "critical" in query or "human" in query:
        response = "This query seems important. I am escalating it to a human agent."
        status = "escalated"
    else:
        response = "Thank you for your query. We are looking into it."
        status = "open"
    return {"response": response, "status": status}

# --- NEW: Direct Ollama AI (No LangChain) ---
def get_direct_ollama_response(query: str):
    print("Attempting to answer using Direct Ollama...")

    # 1. Read the HR Policy file directly
    policy_content = ""
    try:
        with open('./HR_Policy.txt', 'r') as file:
            policy_content = file.read()
    except FileNotFoundError:
        return {"response": "Error: HR_Policy.txt file not found.", "status": "closed"}

    # 2. Create a prompt with the content
    # We feed the whole document to the AI context
    prompt_message = f"""
    You are a helpful HR assistant. Answer the user's question based ONLY on the context provided below.
    
    --- HR POLICY CONTEXT ---
    {policy_content}
    -------------------------
    
    User Question: {query}
    """

    # 3. Send to Ollama
    # Make sure 'llama3' matches the model you pulled (or 'phi-3')
    try:
        response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': prompt_message},
        ])
        
        # 4. Extract the answer
        ai_answer = response['message']['content']
        return {"response": ai_answer, "status": "closed"}
        
    except Exception as e:
        print(f"Ollama Error: {e}")
        raise e # Let the main function handle the fallback

def process_query_with_ai(query: str):
    try:
        return get_direct_ollama_response(query)
    except Exception as e:
        print(f"AI system failed with error: {e}. Falling back to mock AI.")
        return get_mock_ai_response(query)
    