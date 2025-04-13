from django.shortcuts import render
import requests
from textblob import TextBlob  # For sentiment analysis if needed later
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Function to fetch actor summary from Wikipedia
def fetch_wikipedia_summary(actor_name):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{actor_name.replace(' ', '_')}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('extract', '')
    return "No summary found."

# Function to fetch news articles (requires a valid News API key)
def fetch_news_data(actor_name):
    API_KEY = '90b1a839c52c4eac8a12df5333e9c57e'  # Replace with your actual News API key
    url = f"https://newsapi.org/v2/everything?q={actor_name}&language=en&apiKey={API_KEY}"
    response = requests.get(url)
    articles = []
    if response.status_code == 200:
        data = response.json()
        articles = data.get('articles', [])
    return articles

# Function to filter news articles so only those with the actor's name are used
def filter_actor_news(articles, actor_name):
    filtered = []
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        if actor_name.lower() in title.lower() or actor_name.lower() in description.lower():
            filtered.append(article)
    return filtered

def index(request):
    if request.method == 'POST':
        actor_name = request.POST.get('actor_name')
        sentiment_choice = request.POST.get('sentiment_choice', 'negative')  # Default to negative

        # Fetch data from Wikipedia and News API
        wiki_summary = fetch_wikipedia_summary(actor_name)
        news_articles = fetch_news_data(actor_name)
        filtered_articles = filter_actor_news(news_articles, actor_name)
        
        # Combine news descriptions
        news_content = " ".join([article.get('description', '') for article in filtered_articles])

        # Create actor data string
        actor_data = (
            f"Actor: {actor_name}\n"
            f"Wikipedia Summary: {wiki_summary}\n"
            f"News: {news_content}"
        )

        # Dynamic system prompt based on sentiment choice
        system_prompt = (
            "You are a sarcastic commentator. Using the following actor data:\n\n"
            f"{actor_data}\n\n"
            f"Generate exactly 3 human-sounding, {sentiment_choice} sarcastic comments about the actor. "
            "Keep the comments in 10 to 15 words or less. "
            "Make sure to only reference news and data about this actor and do not include any information about other actors."
        )

        # Initialize and run LLM
        llm = Ollama(model="mistral")
        prompt_template = PromptTemplate(input_variables=[], template=system_prompt)
        chain = LLMChain(llm=llm, prompt=prompt_template)
        comments = chain.run({})

        return render(request, 'result.html', {
            'actor': actor_name,
            'comments': comments,
            'sentiment': sentiment_choice
        })
    
    return render(request, 'index.html')