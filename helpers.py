import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json

def format_url(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme and parsed_url.netloc:
        return url
    return "https://" + url

def scrape_website(url):
    url = format_url(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    text = ' '.join([p.get_text() for p in soup.find_all('p')])
    return text.strip()

def get_sentiment(text):
    if not text or len(text.strip()) < 30:
        raise Exception("Text too short to analyze sentiment.")

    prompt = f"Please classify the sentiment of the following text - keep it short and list as 5 bullet points with an emoji:\n\n{text}"
    messages = [
        {"role": "system", "content": "You are a helpful assistant that analyzes the sentiment of text."},
        {"role": "user", "content": prompt}
    ]

    api_key = "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"
    if not api_key:
        raise Exception("Missing OPENAI_API_KEY environment variable.")

    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
    data = json.dumps({
        "model": "gpt-4",
        "messages": messages,
        "max_tokens": 100,
        "temperature": 0.9
    })

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=data)

    try:
        sentiment = response.json()['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError) as e:
        print("OpenAI API Sentiment Error:", response.content)
        raise Exception("An error occurred while processing the sentiment from the OpenAI API.")
    
    return sentiment

def get_summary(text):
    if not text or len(text.strip()) < 50:
        raise Exception("Text too short to summarize.")

    prompt = f"Please summarize the following text in concise bullet points. Use emojis where appropriate:\n\n{text}"
    messages = [
        {"role": "system", "content": "You are a helpful assistant that summarizes and analyses web pages."},
        {"role": "user", "content": prompt}
    ]

    api_key = "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"
    if not api_key:
        raise Exception("Missing OPENAI_API_KEY environment variable.")

    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
    data = json.dumps({
        "model": "gpt-4",
        "messages": messages,
        "max_tokens": 250,
        "temperature": 0.5
    })

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=data)

    try:
        summary = response.json()['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError) as e:
        print("OpenAI API Summary Error:", response.content)
        raise Exception("An error occurred while processing the summary from the OpenAI API.")

    return summary
