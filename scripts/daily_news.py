import os
import datetime
import exa_py
import google.generativeai as genai

# Setup API keys from environment variables
EXA_API_KEY = os.environ.get("EXA_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not EXA_API_KEY or not GEMINI_API_KEY:
    print("Error: EXA_API_KEY or GEMINI_API_KEY not found in environment.")
    exit(1)

# Initialize Exa client and Gemini
exa = exa_py.Exa(EXA_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_daily_news():
    # Search for breaking tech news from the last 24 hours
    one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    search_results = exa.search_and_contents(
        "breaking tech news today",
        type="auto",
        num_results=8,
        start_published_date=one_day_ago
    )
    
    # Format the results for the LLM
    context = ""
    for res in search_results.results:
        context += f"Title: {res.title}\nURL: {res.url}\nContent Snippet: {res.text[:500]}\n---\n"
    
    return context

def summarize_news(news_context):
    today = datetime.date.today().strftime("%B %d, %Y")
    prompt = f"""
    You are a professional tech news curator. Summarize the following news context for {today}.
    
    MANDATES:
    - Automatically create a markdown file (named by the day, e.g., '28.md') in the corresponding 'year/month' directory with the content of web search results after every search.
    - Ensure search results include the related link to the website for each piece of information.
    - Use a less bold format for the markdown content (avoid excessive use of **bold** text).
    
    FORMAT:
    # Breaking Tech News - {today}
    
    Brief intro sentence.
    
    ## Section Title
    - Item description. [Source](URL)
    
    NEWS CONTEXT:
    {news_context}
    """
    
    response = model.generate_content(prompt)
    return response.text

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
    
    print("Done!")

if __name__ == "__main__":
    main()
