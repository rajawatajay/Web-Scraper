import streamlit as st
import requests
# from bs4 import BeautifulSoup
import markdownify
import base64
import re
from urllib.parse import urljoin, urlparse

# Step 1: Custom Styling Function to make the app more visually appealing
def apply_custom_styles():
    st.markdown("""
        <style>
        body {
            font-family: 'Helvetica Neue', sans-serif;
            background-color: #f9f9f9;
            color: #333;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
        }
        .stTextInput input {
            border-radius: 5px;
            padding: 10px;
            border: 1px solid #ddd;
            width: 100%;
            box-sizing: border-box;
        }
        </style>
    """, unsafe_allow_html=True)

# Step 2: Adjust image resource URLs
def adjust_resource_urls(soup, base_url):
    for img_tag in soup.find_all('img'):
        img_url = img_tag.get('src')
        if img_url and not img_url.startswith(('http://', 'https://', '//')):
            img_tag['src'] = requests.compat.urljoin(base_url, img_url)
        elif img_url and img_url.startswith('//'):
            img_tag['src'] = 'https:' + img_url
    return soup

# Step 3: Convert HTML to Markdown
def html_to_markdown(html_content):
    return markdownify.markdownify(
        html_content,
        heading_style="ATX",
        convert=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b', 'i', 'img', 'strong', 'em', 'a']
    )

# Step 4: Clean up Markdown
def clean_markdown(md_content):
    md_content = re.sub(r'\n\s*\n', '\n\n', md_content)
    md_content = '\n'.join(line.strip() for line in md_content.splitlines())
    return md_content.strip()

# Step 5: Download link
import os

def download_markdown(system_prompt, scraped_content, filename="LLM_Input.md"):
    content_str = str(scraped_content)
    b64 = base64.b64encode(content_str.encode()).decode()
    combined_content = f"""## System Prompt"""
    # Define the download folder
    # Encode for download link
    b64 = base64.b64encode(combined_content.encode()).decode()

    # Optional: Save to local file system (adjust the path if needed)
    download_folder = "downloads"  # You can change this folder name
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    file_path = os.path.join(download_folder, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(combined_content)
    
    href = f"""<a href="data:file/markdown;base64,{b64}" download="{filename}">
    <button style="
        display: inline-block;
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        text-align: center;
        font-size: 16px;
        cursor: pointer;
        border-radius: 5px;
        border: none;">
        Download Markdown File
    </button>
    </a>
    """
    return href

# Step 6: Find internal links
def get_internal_links(base_url, soup):
    base_domain = urlparse(base_url).netloc
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc == base_domain:
            links.add(full_url.split('#')[0])
    return list(links)

# Step 7: Main App
def main():
    apply_custom_styles()

    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            min-width: 350px;
            max-width: 400px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🕷️ Web Scraper App - Crawl Internal Pages & Export Markdown")

    # Sidebar inputs
    with st.sidebar:
        st.header("🔧 Settings")

        # Initialize URL history in session_state
        if "url_history" not in st.session_state:
            st.session_state.url_history = []

        # URL input with suggestion from history
        selected_url = st.selectbox("🌐 Previously Used URLs:", st.session_state.url_history[::-1], index=0) if st.session_state.url_history else ""
        url = st.text_input("🌐 Enter the URL to scrape:", value=selected_url)

                # Default prompt suggestions
        default_prompts = [
            "You are a healthcare assistant. Provide suggestions based on symptoms shared by the user.",
            "You are a virtual doctor. Ask follow-up questions based on the user's medical concerns.",
            "You are a nutritionist. Suggest a diet plan for users with diabetes or obesity.",
            "You are a fitness expert. Provide a weekly workout plan for weight loss and general wellness."
        ]

        st.subheader("💬 Choose a Default Prompt")
        selected_prompt = st.selectbox("🧠 Pick a predefined health assistant prompt:", [""] + default_prompts)

        system_prompt = st.text_area(
            "✍️ System Prompt for LLM:",
            value=selected_prompt if selected_prompt else "",
            height=150,
            placeholder="Enter your custom prompt or select from above..."
        )


        if system_prompt:
            try:
                with open("system_prompt.py", "w", encoding="utf-8") as f:
                    f.write('"""' + system_prompt + '\n\n' + '"""')
                st.sidebar.success("System prompt saved!")
            except Exception as e:
                st.sidebar.error(f"Error saving prompt: {e}")

        run_scraper = st.button("🚀 Run Web Scraper")

    if run_scraper:
        if url:
            # Save to history if not already present
            if url not in st.session_state.url_history:
                st.session_state.url_history.append(url)

            try:
                visited = set()
                all_md_content = ""

                with st.spinner("Scraping in progress... please wait ⏳"):

                    def crawl(link):
                        if link in visited:
                            return "", None
                        visited.add(link)
                        res = requests.get(link)
                        res.raise_for_status()
                        soup = BeautifulSoup(res.content, 'html.parser')
                        soup = adjust_resource_urls(soup, link)
                        article = soup.find('article') or soup.body
                        html_content = str(article)
                        md = clean_markdown(html_to_markdown(html_content)).replace('"""', '')
                        with open("system_prompt.py", "a", encoding="utf-8") as f:
                            f.write("\n\n" + '"""' + md + "\n\n" + '"""')
                        return soup, md

                    # Initial crawl
                    initial_response = requests.get(url)
                    initial_response.raise_for_status()
                    initial_soup = BeautifulSoup(initial_response.content, 'html.parser')

                    internal_links = get_internal_links(url, initial_soup)
                    internal_links.insert(0, url)  # include homepage

                    for link in internal_links:
                        soup, md = crawl(link)
                        if md:
                            all_md_content += f"\n\n---\n\n## Scraped from: {link}\n\n" + md

                st.success("✅ Scraping complete and your system prompt has been updated")
                st.markdown(all_md_content)

            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching the URL: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
        else:
            st.warning("⚠️ Please enter a valid URL.")

# Step 8: Run the app
if __name__ == "__main__":
    main()