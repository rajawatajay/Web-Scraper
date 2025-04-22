import os
import json
import requests
import re
import streamlit as st
from helpers import format_url, scrape_website, get_summary, get_sentiment


def get_generated_url(prompt):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates URLs based on user input."},
        {"role": "user", "content": prompt}
    ]
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'
    }
    data = json.dumps({
        "model": "gpt-4",
        "messages": messages,
        "max_tokens": 50,
        "n": 1,
        "stop": None,
        "temperature": 0.5
    })

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=data)
    print("API Response:", response.json())

    try:
        generated_text = response.json()['choices'][0]['message']['content'].strip()
    except KeyError:
        print("Error in OpenAI API response:", response.content)
        raise Exception("An error occurred while processing the generated URL from the OpenAI API.")

    # Extract URL from the generated text
    url_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', generated_text)
    if url_match:
        return format_url(url_match.group(0))
    else:
        print("Generated text:", generated_text)
        raise Exception(f"No URL was found in the generated text: '{generated_text}'")


st.title("📰 URL Summarizer")

source_option = st.radio("Choose a source option:", ("Enter a URL or keyword"))


if source_option == "Enter a URL or keyword":
    url_input = st.text_input("Enter a URL or keyword:")
    selected_url = None
else:
    selected_website = st.selectbox("Choose from the pre-listed UK news websites:", list(url_mapping.keys()))
    selected_url = url_mapping[selected_website]
    url_input = None

if st.button("Submit"):
    if url_input:
        # Check if it's already a full URL
        if url_input.startswith("http://") or url_input.startswith("https://") or "www." in url_input:
            url = format_url(url_input)
        else:
            with st.spinner("Generating URL based on input..."):
                try:
                    url = get_generated_url(url_input)
                except Exception as e:
                    st.error(f"Failed to generate a URL from your input: {e}")
                    st.stop()
    else:
        url = format_url(selected_url)

    st.write(f"🔍 Processing URL: {url}")

    try:
        with st.spinner("Scraping website and generating summary..."):
            content = scrape_website(url)
            summary = get_summary(content)
            sentiment = get_sentiment(summary)
    except Exception as e:
        st.error(f"An error occurred during processing: {e}")
    else:
        st.subheader("🧠 Content")
        
        st.write(content)
        st.subheader("🧠 Sentiment")
        st.write(sentiment)
        st.subheader("📝 Summary")
        st.write(summary)
