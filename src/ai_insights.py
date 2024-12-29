import openai
import os

def generate_ai_insights(orders, inventory_df):
    """
    Generates an AI-based summary of sales & popular items using the ChatCompletion endpoint.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return "Error: The OPENAI_API_KEY environment variable is not set."

    total_sales = sum(o["total_cost"] for o in orders)
    if not inventory_df.empty:
        most_popular = inventory_df.sort_values(by="popularity", ascending=False).iloc[0]["name"]
    else:
        most_popular = "No products"

    prompt = f"""
We have total sales of ${total_sales}.
The most popular item is: {most_popular}.
Please provide a concise strategy to increase overall sales.
    """

    try:
        # Use ChatCompletion with a chat-based model (e.g. gpt-3.5-turbo)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        # The AI response is in response["choices"][0]["message"]["content"]
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"
