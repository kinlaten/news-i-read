import os
import datetime
import exa_py
import requests
from google import genai

# Setup API keys from environment variables
EXA_API_KEY = os.environ.get("EXA_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

if not EXA_API_KEY or not GEMINI_API_KEY:
    print("Error: EXA_API_KEY or GEMINI_API_KEY not found in environment.")
    exit(1)

# Initialize Exa client and Gemini
exa = exa_py.Exa(EXA_API_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)


def get_daily_news():
    # Search for breaking tech news from the last 24 hours
    one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    search_results = exa.search_and_contents(
        "breaking tech news today",
        type="auto",
        num_results=8,
        start_published_date=one_day_ago,
    )

    # Format the results for the LLM
    context = ""
    for res in search_results.results:
        context += f"Title: {res.title}\nURL: {res.url}\nContent Snippet: {res.text[:500]}\n---\n"

    return context


def summarize_news(news_context):
    today = datetime.date.today().strftime("%B %d, %Y")

    # Fetch mandates from both local and global sources
    mandates = []

    # Global ~/.gemini/GEMINI.md
    global_path = os.path.expanduser("~/.gemini/GEMINI.md")
    if os.path.exists(global_path):
        try:
            with open(global_path, "r") as f:
                mandates.append(f"--- GLOBAL MANDATES ---\n{f.read()}")
        except Exception as e:
            print(f"Warning: Could not read global GEMINI.md: {e}")

    # Local GEMINI.md
    local_path = "GEMINI.md"
    if os.path.exists(local_path):
        try:
            with open(local_path, "r") as f:
                mandates.append(f"--- LOCAL MANDATES ---\n{f.read()}")
        except Exception as e:
            print(f"Warning: Could not read local GEMINI.md: {e}")

    combined_mandates = "\n\n".join(mandates)

    prompt = f"""
    You are a professional tech news curator. Summarize the following news context for {today}.
    
    MANDATES FROM PROJECT CONFIGURATION:
    {combined_mandates}

    ADDITIONAL FORMATTING RULES:
    - Use a less bold format (avoid excessive use of **bold** text).
    - DO NOT wrap the output in markdown code blocks (e.g., ```markdown or ```).
    - Return RAW markdown text only.
    
    FORMAT:
    # Breaking Tech News - {today}
    
    Brief intro sentence.
    
    ## Section Title
    - Item description. [Source](URL)
    
    NEWS CONTEXT:
    {news_context}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite", contents=prompt
    )
    return response.text


def send_to_discord(content):
    if not DISCORD_WEBHOOK_URL:
        print("No Discord Webhook URL found, skipping notification.")
        return

    # Discord has a 2000 character limit per message
    if len(content) > 1900:
        content = content[:1900] + "\n\n... (Truncated. Check GitHub for full report)"

    payload = {"content": content}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Successfully sent to Discord!")
    except Exception as e:
        print(f"Error sending to Discord: {e}")


def main():
    print("Fetching tech news...")
    news_context = get_daily_news()

    print("Summarizing news...")
    summary = summarize_news(news_context)

    # Determine the directory and file path
    now = datetime.datetime.now()
    year_dir = str(now.year)
    month_dir = str(now.month)
    day_file = f"{now.day}.md"

    full_path = os.path.join(year_dir, month_dir, day_file)
    os.makedirs(os.path.join(year_dir, month_dir), exist_ok=True)

    print(f"Saving news to {full_path}...")
    with open(full_path, "w") as f:
        f.write(summary)

    print("Sending to Discord...")
    send_to_discord(summary)

    print("Done!")


if __name__ == "__main__":
    main()
