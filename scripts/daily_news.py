import os
import datetime
import exa_py
import requests
from google import genai
import config

EXA_API_KEY = os.environ.get("EXA_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not EXA_API_KEY or not GEMINI_API_KEY:
    print("Error: EXA_API_KEY or GEMINI_API_KEY not found in environment.")
    exit(1)

# Initialize Exa client and Gemini
exa = exa_py.Exa(EXA_API_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)


def get_daily_news(query):
    # Search for breaking news from the last 24 hours
    one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    search_results = exa.search_and_contents(
        query,
        type="auto",
        num_results=config.EXA_NUM_RESULTS,
        start_published_date=one_day_ago,
    )

    context = ""
    for res in search_results.results:
        context += f"Title: {res.title}\nURL: {res.url}\nContent Snippet: {res.text[:config.EXA_SNIPPET_LENGTH]}\n---\n"

    return context


def summarize_news(news_context, category_name):
    today = datetime.date.today().strftime("%B %d, %Y")

    mandates = []

    global_path = os.path.expanduser("~/.gemini/GEMINI.md")
    if os.path.exists(global_path):
        try:
            with open(global_path, "r") as f:
                mandates.append(f"--- GLOBAL MANDATES ---\n{f.read()}")
        except Exception as e:
            print(f"Warning: Could not read global GEMINI.md: {e}")

    local_path = "GEMINI.md"
    if os.path.exists(local_path):
        try:
            with open(local_path, "r") as f:
                mandates.append(f"--- LOCAL MANDATES ---\n{f.read()}")
        except Exception as e:
            print(f"Warning: Could not read local GEMINI.md: {e}")

    combined_mandates = "\n\n".join(mandates)

    prompt = f"""
    You are a professional news curator specializing in {category_name}. 
    Summarize the following news context for {today} within 2000 characters
    
    MANDATES FROM PROJECT CONFIGURATION:
    {combined_mandates}

    ADDITIONAL FORMATTING RULES:
    - Use a less bold format (avoid excessive use of **bold** text).
    - DO NOT wrap the output in markdown code blocks (e.g., ```markdown or ```).
    - Return RAW markdown text only.
    
    FORMAT:
    # {category_name} - {today}
    
    Brief intro sentence summarizing the day's vibe.
    
    ## Section Title
    - Item description. [Source](URL)
    
    NEWS CONTEXT:
    {news_context}
    """

    response = client.models.generate_content(
        model=config.GEMINI_MODEL, contents=prompt
    )
    return response.text


def send_to_discord(content, webhook_env):
    webhook_url = os.environ.get(webhook_env)
    if not webhook_url:
        print(f"No webhook found for {webhook_env}, skipping Discord notification.")
        return

    if len(content) > config.DISCORD_MAX_CHARS:
        content = (
            content[: config.DISCORD_MAX_CHARS]
            + "\n\n... (Truncated. Check GitHub for full report)"
        )

    payload = {"content": content}
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print(f"Successfully sent {webhook_env} to Discord!")
    except Exception as e:
        print(f"Error sending to Discord ({webhook_env}): {e}")


def main():
    all_summaries = []

    for category in config.NEWS_CATEGORIES:
        name = category["name"]
        query = category["query"]
        webhook_env = category["webhook_env"]
        save_to_file = category.get(
            "save_to_file", True
        )  # Default to True if not specified

        print(f"Processing category: {name}...")

        print(f"  Fetching news for '{name}'...")
        news_context = get_daily_news(query)

        print(f"  Summarizing '{name}'...")
        summary = summarize_news(news_context, name)

        # Only add to the list of summaries for the .md file if flagged
        if save_to_file:
            all_summaries.append(summary)

        print(f"  Sending '{name}' to Discord...")
        send_to_discord(summary, webhook_env)

    if all_summaries:
        full_report = "\n\n---\n\n".join(all_summaries)

        now = datetime.datetime.now()
        year_dir = str(now.year)
        month_dir = str(now.month)
        day_file = f"{now.day}.md"

        full_path = os.path.join(year_dir, month_dir, day_file)
        os.makedirs(os.path.join(year_dir, month_dir), exist_ok=True)

        print(f"Saving report for selected categories to {full_path}...")
        with open(full_path, "w") as f:
            f.write(full_report)
    else:
        print("No categories marked for file saving, skipping .md file creation.")

    print("Done!")


if __name__ == "__main__":
    main()
