import time
import os
import asyncio
import re
import google.generativeai as genai
from dotenv import load_dotenv
import csv
from playwright.async_api import async_playwright
import argparse
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from urllib.parse import urljoin

# --- Main Application Logic ---

def get_google_image(tool_name: str) -> str:
    print(f"Searching Google Images for '{tool_name} logo'...")
    search_url = f"https://www.google.com/search?tbm=isch&q={tool_name.replace(' ', '+')}+logo"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        # Find all img tags and return the first with a direct http/https src
        for img_tag in soup.find_all("img"):
            src = img_tag.get("src")
            if src and src.startswith("http"):
                return src
            # Some images may use data-src for lazy loading
            data_src = img_tag.get("data-src")
            if data_src and data_src.startswith("http"):
                return data_src
    except Exception as e:
        print(f"Error fetching Google image: {e}")
    return ""


# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
CSV_OUTPUT_DIR = "output_csv"
HTML_OUTPUT_DIR = "output_html_gemini"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

genres = [
    "AI Workflow", "AI Recruiting", "AI Customer Service", "Personal AI Assistant",
    "Voice AI Agents", "AI Sales Agent", "AI Agent Platform", "AI Coding Assistants",
    "AI Webinar Script Assistants", "AI Product Description Writers", "AI Logo Makers",
    "AI Online Course Creators", "AI Print-on-Demand Designers", "AI Dropshipping Automation",
    "AI Form and Survey Builders", "AI Social Media Schedulers", "AI Video Editors",
    "AI Automation Tools", "AI App Builders", "AI Website Builders", "AI Email Marketing",
    "AI No Code Tools", "AI Code Review Tools", "AI Predictive Analytics", "AI Data Analytics",
    "AI Project Management Tools", "AI Workflow Automation", "AI Personal Assistants",
    "AI Language Translation", "AI Transcription Tools", "AI SEO Tools", "AI Email Assistants",
    "AI Text-to-Speech Tools", "AI Voice Generators", "AI Presentation Makers",
    "AI Design Generators", "AI Music Generators", "AI Open Source & LLMs",
    "AI Learning & Certifications", "AI Events", "AI Project Investors",
    "AI Content Generators", "AI Chatbots", "AI Image Generators", "AI Frameworks",
    "AI Video Generators", "AI Marketing Tools", "AI Image Recognition", "AI Framework",
    "AI Chatbot Builders", "AI Viral Tweet Generators", "AI Document Summarization",
    "AI Social Media Management", "AI Customer Support Automation", "AI Virtual Meeting Assistants",
    "AI for Productivity", "AI Resume Builders", "E-Commerce Store Builders AI",
    "AI Writing Assistants", "AI Research", "AI Courses", "AI News", "AI Resources",
    "AI Tools", "AI Mental Health & Wellness", "Crypto Wallet Trackers / Multi-wallet Monitors",
    "Crypto Security Tools", "Crypto Blockchain Development Platforms",
    "Crypto Token Analytics Platforms", "Crypto Blockchain Explorers",
    "Crypto Launchpads (IDO/ICO Platforms)", "Crypto Centralized Exchanges (CEXs)",
    "Crypto Arbitrage Tools", "Crypto Lending Platform", "Crypto Trading & Sniping Bots",
    "Crypto Liquid Staking Derivatives", "Crypto Coin Tracker & Stats",
    "Crypto Initial Coin Offerings (ICOs)", "Crypto KYC and On-chain Identities",
    "Crypto Environmental", "Crypto Blockchain", "Crypto Smart Contracts", "Crypto Tokenomics",
    "Crypto Games", "Crypto Directories", "Crypto Entertainment",
    "Crypto Augmented Reality & Virtual Reality (AR/VR)", "Crypto Passive Income",
    "Crypto Earn Money and Crypto", "Crypto DYOR Club & Fundamental Reviews", "Crypto eBooks",
    "Crypto Businesses", "Crypto Open Source & APIs", "Crypto Jobs", "Crypto Help-a-thon",
    "Crypto Non-Profits", "Crypto Project Investors", "Crypto DAOs",
    "Crypto Hardware / Security / Support", "Crypto Learning & Certificates", "Crypto Metaverse",
    "Crypto Real Estate", "Crypto Technical Analysis (TA)", "Crypto Real World Assets",
    "Crypto Events", "Crypto Staking & Yield Farming", "Crypto News",
    "Crypto Affiliates - Get Chat Paid", "Crypto Mining", "Crypto Financial & Legal",
    "Crypto Airdrops", "Crypto Courses", "Crypto NFT Marketplace", "Crypto Gameshows",
    "Crypto Health & Safety", "Crypto Tools", "Crypto Resources"
]

PLAN_TEMPLATE = r'''
    📘 Tool Name: [tool name]
    🔗 Official Site: [url]
    🎥 Explainer Video: [youtube video link]
    🧑‍💻 AIC Contributor: AIC Community


    🧩 Quick Look: [Simple breakdown - keep it to under 7 words]
    Beginner Benefit: [Simple breakdown - keep it to under 7 words]

    🌟 [tool name] 101:
    [explainer 101 section - give brief breakdown. 2 paragraphs, 3 sentences each.]

    📚 Key AI Concepts Explained:
    [list 3 bullet points of different concepts to consider when using this tool. Make each bullet point
    a single sentence (1-2 sentences)]

    📖 Words to Know:
    [list 3 bullet points of different words to know when using this tool. Make each bullet point a
    single sentence (8-12 words)]

    🎯 Imagine This:
    [give an analogy that a normal person would understand. 1 sentence.]
    [give an analogy that a normal person would understand. 1 sentence.]

    🌟 Fun Fact About the Tool:
    [Provide a surprising or little-known fun fact about the tool, its history, or its creators. 1 sentence.]
    [Provide a surprising or little-known fun fact about the tool, its history, or its creators. 1 sentence.]
    [Provide a surprising or little-known fun fact about the tool, its history, or its creators. 1 sentence.]

    ✅ Pros:
    ● [3 bullet points of pros - 8-12 words]

    ❌ Cons:
    ● [3 bullet points of cons - 8-12 words]

    🧪 Use Cases:
    1. [3 bullet points of use cases - 8-12 words]

    💰 Pricing Breakdown:
    [Based on the scraped text, find and summarize the tool's pricing structure. Mention if there is a free trial or free tier. If no pricing is found, state that pricing information was not readily available on the homepage.]

    🌟 Real-World Examples:
    [Provide 3 relatable, real-world examples of how a beginner (like a student, a small business owner, or a content creator) might use this tool. 1-2 sentences each, focusing on practical outcomes.]

    💡 Initial Warnings:
    ● [3 bullet points of initial warning a new user should consider before signing up. 1-2
    sentences 12-20 words]




    🚀 Getting Started:
    1. [3-6 numbered steps on how to get started. 1 sentence per step (8-12 words). Include
    affiliate link and steps users have to do to sign up]

    💡 Power-Ups:
    ● [3 bullet points for more advanced users. 1-2 sentence answer (15-20 words per
    sentence)]

    🎯 Difficulty Score: [Rank from 1-10]/10 [Emoji] ([Descriptor])
    [1 paragraph, 4 sentences. Provide a ranking score for someone new to using this. 1 being super easy, 10 being advanced expert. Rank usability, enjoyment, benefits of use, skills needed to use this, benefit and negative. Do not make false claims on anything throughout the content]

    <p></p>

    ⭐ Official AI-Driven Rating: [Rank from 1-10]/10
    [1 paragraph, 4 sentences. Provide a ranking score for someone new to using this. 1 being super easy, 10 being advanced expert. Give your unbiased opinion. Do not make false claims on anything throughout the content. Mention why you like it. Show points awarded and deducted to prove why you gave this score.]

    <hr />

    🔎 Deeper Look at [tool name]

    🎯 Why [tool name] is Ideal for [Specific Audience]

        <p>Ready to level up your workflow? [tool name] is the AI sidekick you’ve been waiting for. Whether you’re a solo creator building the next big thing or part of a large team, [tool name] is designed to make your life easier. Think of it as a tireless assistant that’s fluent in the tasks you need to accomplish.</p>
        <p>For [Specific Audience], [tool name] is a game-changer. It’s not just about working faster; it’s about working *smarter*. [tool name] can help you brainstorm solutions to complex problems, automate tedious tasks, and even learn new skills on the fly.</p>
        <p>But it’s not just for beginners. Seasoned professionals can use [tool name] to streamline their process, generate boilerplate content, and explore new creative avenues. It’s like having an expert on call 24/7, ready to offer suggestions and insights. By handling the grunt work, [tool name] frees you up to focus on what really matters: creating amazing things.</p>

    <p></p>

    🔑 Key Features of [tool name]: In-Depth Breakdown

    [tool name] is more than just a simple tool. It’s a powerful platform with a suite of features designed to supercharge your workflow. Let’s dive into some of the key features that make [tool name] a must-have.

    Feature 1: [Brief Feature Title]
    [Detailed description of the feature, its benefits, and how it works. Explain what makes this feature stand out and why it's valuable to the user. Use real-world examples if possible.]

    Feature 2: [Brief Feature Title]
    [Detailed description of the feature, its benefits, and how it works. Explain what makes this feature stand out and why it's valuable to the user. Use real-world examples if possible.]

    Feature 3: [Brief Feature Title]
    [Detailed description of the feature, its benefits, and how it works. Explain what makes this feature stand out and why it's valuable to the user. Use real-world examples if possible.]

    🚀 Real-World Case Studies Using [tool name]

    Don’t just take our word for it. Here are a few real-world examples of how people are using [tool name] to do amazing things.

        <p>Startup Saves Hours on [Task]: A small startup was struggling to keep up with their content creation. By using [tool name] to generate ideas and draft initial content, they were able to save over 10 hours per week. This allowed them to focus on their core product and ship features faster.</p>
        <p>Student Aces a Project: A student with no prior experience in [field] wanted to build a project for a class. Using [tool name], they were able to learn the basics and build a functional prototype in just a few days.</p>
        <p>Open Source Project Improves Documentation: A popular open-source project was struggling with outdated documentation. By using [tool name] to help write and revise their docs, they were able to create a more welcoming and accessible resource for their community.</p>
    ❓ FAQ - 5 questions and answers that are trending on Google that need answers.

    1.  Is [tool name] better than [Competitor]?
        While both are excellent, [tool name]’s specific features for [task] give it an edge. Its intuitive interface and powerful automation capabilities can be a huge advantage for [Specific Audience].

    2.  How much does [tool name] cost?
        [tool name] offers a variety of pricing plans, including a free tier for getting started. For more advanced features, they offer paid plans that are competitively priced.

    3.  Can [tool name] help me with [specific task]?
        Absolutely! [tool name] is a fantastic tool for [specific task]. You can describe what you need, and [tool name] will help you get it done.

    4.  Is [tool name] safe to use with my data?
        The creators of [tool name] have robust privacy and security measures in place to protect your data. However, it’s always a good idea to be cautious when sharing sensitive information with any third-party service.

    5.  How can I get started with [tool name]?
        Getting started with [tool name] is easy! Just head over to their website and you can sign up for a free account and start exploring its features right away.

    ⚖️ Stay Safe:
    The tools and information on this site are aggregated from community contributions and internet sources. We strongly recommend users independently verify all details, consult original resources for accuracy, and exercise caution. The information, including company profiles, pricing, rules, and structures, is based on current knowledge as of 12:55 PM EDT on Friday, August 22, 2025, and is subject to change at the discretion of the respective entities.

    This site is provided "as-is" with no warranties, and no professional, financial, or legal advice is offered or implied. We disclaim all liability for errors, omissions, damages, or losses arising from the use of this information. This platform is intended to showcase tools for informational purposes only and does not endorse or advise on financial investments or decisions. Users must conduct their own due diligence (DYOR), verify the authenticity of tool websites to avoid phishing scams, and secure accounts with strong passwords and two-factor authentication.

    AIC is not responsible for the performance, safety, outcomes, or risks associated with any listed tools. Some links on this site may be affiliate links, meaning we may earn a commission if you click and make a purchase, at no additional cost to you. Always research thoroughly, comply with local laws and regulations, and consult qualified financial or legal professionals before taking action to understand potential risks. Nothing herein constitutes professional advice, and all decisions are at the user’s sole discretion. This disclaimer is governed by the laws of St. Petersburg, Florida, USA.
'''

# --- Main Application Logic ---

async def scrape_website(url: str) -> tuple[str, str]:
    """
    Asynchronously scrapes the text and HTML content of a given URL.
    Returns a tuple of (text_content, html_content).
    """
    print(f"Scraping {url}...")
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            
            # Look for a pricing link and click it
            try:
                pricing_link = page.get_by_role("link", name=re.compile(r"pricing|plans", re.IGNORECASE)).first
                if await pricing_link.is_visible():
                    print("Found pricing/plans link, navigating...")
                    await pricing_link.click()
                    await page.wait_for_load_state("networkidle", timeout=30000)
            except Exception as e:
                print(f"No pricing/plans link found or error navigating: {e}")

            text_content = await page.locator('body').inner_text()
            html_content = await page.content()
            await browser.close()
            print("Scraping complete.")
            return text_content, html_content
    except Exception as e:
        print(f"Error scraping website: {e}")
        return "", ""

def find_image_url(html_content: str, base_url: str) -> str:
    """
    Parses HTML to find the best representative image URL.
    """
    if not html_content:
        return ""
    print("Finding best image URL...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Prioritize Open Graph image
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        return urljoin(base_url, og_image['content'])

    # Look for a logo
    logo = soup.find('img', alt=lambda x: x and 'logo' in x.lower())
    if logo and logo.get('src'):
        return urljoin(base_url, logo['src'])

    # Fallback to the first large image
    for img in soup.find_all('img'):
        if img.get('width') and img.get('height'):
            try:
                if int(img['width']) > 100 and int(img['height']) > 100:
                    return urljoin(base_url, img['src'])
            except (ValueError, TypeError):
                continue
    
    print("No suitable image found.")
    return ""

def find_youtube_video(tool_name: str) -> str:
    """
    Searches YouTube for a relevant tutorial or explainer video.
    """
    if not YOUTUBE_API_KEY:
        print("YouTube API key not found. Skipping video search.")
        return ""
        
    print(f"Searching for YouTube video for '{tool_name}'...")
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        search_response = youtube.search().list(
            q=f"{tool_name} overview explainer review",
            part='snippet',
            maxResults=5,
            type='video'
        ).execute()
        
        videos = search_response.get('items', [])
        if not videos:
            print("No relevant YouTube videos found.")
            return ""
            
        # Simple heuristic: return the first result
        video_id = videos[0]['id']['videoId']
        return f"https://www.youtube.com/watch?v={video_id}"

    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return ""

def get_trending_questions(tool_name: str) -> str:
    """
    Scrapes Google Search for "People also ask" questions.
    Note: This is dependent on Google's HTML structure and may break if they change it.
    """
    print(f"Searching for trending questions for '{tool_name}'...")
    try:
        search_url = f"https://www.google.com/search?q={tool_name.replace(' ', '+')}+questions"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        questions = []
        # Selectors for "People also ask" questions. These may change.
        # Common selectors found in Google search results.
        selectors = [
            "div.related-question-pair", # A common container for PAA
            "div.wQ3Ihd", # Another possible selector
            "div.V3FYCf" # And another
        ]

        for selector in selectors:
            question_divs = soup.select(selector)
            for div in question_divs:
                question = div.get_text(strip=True)
                if question.endswith('?'):
                    questions.append(question)
            if questions:
                break # Stop if we found questions with one selector

        if questions:
            unique_questions = list(dict.fromkeys(questions))
            return "\n".join(unique_questions[:5])

    except Exception as e:
        print(f"Error fetching trending questions: {e}")
    
    return ""


def convert_links(content: str) -> str:
    """
    Converts markdown style links to plain URLs (removes markdown and HTML link formatting).
    """
    # Remove markdown links, keep only the URL
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    return re.sub(pattern, r'\2', content)


def get_genre_with_gemini(scraped_text: str) -> str:
    """
    Uses Gemini to determine the best genres for a tool based on its scraped text.
    """
    print("Determining genre with Gemini...")
    genai.configure(api_key=GEMINI_API_KEY)
    
    model = genai.GenerativeModel('gemini-2.5-flash')

    genres_str = ", ".join(genres)

    prompt = f"""
    Based on the following text from a tool's website, which of these categories best describe it?
    Categories: {genres_str}

    Please respond with a comma-separated list of the most relevant genres from the list. You can return up to 3 genres. Do not respond with just "AI" or "Crypto".

    Website text:
    {scraped_text[:4000]}
    """
    
    try:
        response = model.generate_content(prompt)
        suggested_genres_str = response.text.strip()
        print(f"Gemini raw response for genre: {suggested_genres_str}")
        
        # Validate the response from Gemini
        suggested_genres = [genre.strip() for genre in suggested_genres_str.split(',')]
        
        valid_genres = []
        # Create a set of normalized genres for efficient lookup
        normalized_genres = {g.strip().lower() for g in genres}
        
        for genre in suggested_genres:
            normalized_suggested_genre = genre.strip().lower()
            if normalized_suggested_genre in normalized_genres and normalized_suggested_genre not in ['ai', 'crypto']:
                # Find the original casing from the 'genres' list to return
                original_genre = next((g for g in genres if g.strip().lower() == normalized_suggested_genre), None)
                if original_genre:
                    valid_genres.append(original_genre)
        
        if valid_genres:
            print(f"Gemini genre suggestion: {valid_genres[0]}")
            return valid_genres[0]
        else:
            print(f"Gemini returned invalid or broad genres: {suggested_genres_str}.")
            return ""
            
    except Exception as e:
        print(f"Error determining genre with Gemini: {e}")
        return ""

def generate_content_with_gemini(scraped_text: str, tool_name: str, tool_url: str, contributor: str, plan_template: str, image_url: str, video_url: str, trending_questions: str) -> str:
    """
    Generates content using Google's Gemini model based on a template and scraped text.
    """
    print("Generating content with Gemini...")
    genai.configure(api_key=GEMINI_API_KEY)
    
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    You are a content creator for a tech blog. Your task is to create a blog post about a new tool, meticulously following the provided template's structure and formatting. Your writing style should be simple, accessible, and engaging, as if you're explaining the tool to a friend who is new to the tech space. Avoid jargon wherever possible.

    **CRITICAL INSTRUCTIONS:**
    1.  **PRESERVE ALL HTML AND SPACING:** Your response must replicate the exact HTML structure of the template, including all `<p>` tags, `<hr />` tags, and newlines to ensure proper spacing between sections.
    2.  **NO PLACEHOLDERS:** You must write out the full text for all sections. Do NOT use placeholders like "[Same as the original template's Stay Safe section]". Generate the complete content for every field.
    3.  **START IMMEDIATELY:** The response must begin *directly* with "📘 Tool Name:", with no preceding text.
    4.  **NO CODE BLOCKS:** Do not wrap your response in markdown code fences like ```html or ```.
    5.  **NUMBERED LISTS:** All lists (like under Pros, Cons, etc.) MUST be numbered (e.g., 1., 2., 3.).
    6.  **PLAIN LINKS ONLY:** All links MUST be plain URLs, not HTML or markdown links.
    7.  **USE PROVIDED LINKS:** You MUST use the provided Image URL and Video URL in the final output. If a URL is empty, state that a suitable one could not be found.

    **Template:**
    {plan_template}

    **Tool Information:**
    - Tool Name: {tool_name}
    - Tool URL: {tool_url}
    - Contributor: {contributor}
    - Image URL: {image_url}
    - Video URL: {video_url}
    - Trending Questions: {trending_questions}
    - Scraped Content from Website: {scraped_text[:8000]}

    Generate the full blog post based on the template, following all instructions perfectly.
    """
    
    try:
        response = model.generate_content(prompt)
        print("Content generation complete.")
        return response.text
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return ""

def save_as_html(content: str, tool_name: str):
    """
    Saves the generated content as an HTML file for previewing.
    """
    if not os.path.exists(HTML_OUTPUT_DIR):
        os.makedirs(HTML_OUTPUT_DIR)
    
    file_path = os.path.join(HTML_OUTPUT_DIR, f"{tool_name.replace(' ', '_').lower()}.html")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved HTML preview to {file_path}")

def save_tool_as_csv(data: dict, file_path=None, write_header=False):
    """
    Creates a CSV row for a tool. If file_path is provided, appends to that file. If write_header is True, writes header first.
    """
    if not os.path.exists(CSV_OUTPUT_DIR):
        os.makedirs(CSV_OUTPUT_DIR)

    headers = [
        "Title","Author","Excerpt","Thumbnail","Language","Genres","Tags","Portrait Image","Movie Method","Movie URL","Content","Status"
    ]
    row = {h: "" for h in headers}
    row["Title"] = data.get("tool_name", "Canva")
    row["Author"] = data.get("contributor", "TechCEO")
    row["Excerpt"] = data.get("excerpt", "A short summary for Canva.")
    row["Thumbnail"] = data.get("image_url", "https://media.istockphoto.com/id/636379014/photo/hands-forming-a-heart-shape-with-sunset-silhouette.jpg?s=612x612&w=0&k=20&c=CgjWWGEasjgwia2VT7ufXa10azba2HXmUDe96wZG8F0=")
    row["Language"] = data.get("language", "en")
    row["Genres"] = data.get("category", "")
    row["Tags"] = data.get("tags", "design,graphics")
    row["Portrait Image"] = data.get("portrait_image", row["Thumbnail"])
    row["Movie Method"] = "Movie URL"
    row["Movie URL"] = data.get("video_url", "https://www.youtube.com/watch?v=F2xt7o1JqNw")
    row["Content"] = data.get("generated_content", "This is a test post for Canva. If this uploads, we can add more fields.")
    row["Status"] = "publish"
    if file_path:
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_ALL, delimiter=',')
            if write_header:
                writer.writeheader()
            writer.writerow(row)
    else:
        tool_name = data.get("tool_name", "untitled")
        file_name = tool_name.replace(' ', '_').lower()
        file_path = os.path.join(CSV_OUTPUT_DIR, f"{file_name}_post.csv")
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_ALL, delimiter=',')
            writer.writeheader()
            writer.writerow(row)
        print(f"Successfully created CSV for WordPress: {file_path}")



async def main(args):
    """
    Main function to run the automation.
    """
    scraped_text, scraped_html = await scrape_website(args.url)
    if not scraped_text:
        return

    genre = get_genre_with_gemini(scraped_text)
    image_url = find_image_url(scraped_html, args.url)
    if not image_url:
        image_url = get_google_image(args.name)
    video_url = find_youtube_video(args.name)
    trending_questions = get_trending_questions(args.name)

    generated_content = generate_content_with_gemini(
        scraped_text, args.name, args.url, args.contributor, PLAN_TEMPLATE, image_url, video_url, trending_questions
    )
    if not generated_content:
        return
    
    generated_content = convert_links(generated_content)
        
    save_as_html(generated_content, args.name)

    # Fill all fields to match sample format, using user/tool info where possible
    data_for_csv = {
        "tool_name": args.name,
        "contributor": args.contributor,
        "category": genre,
        "generated_content": generated_content,
        "image_url": image_url,
        "video_url": video_url,
        "tool_url": args.url,
        "excerpt": f"A quick look at {args.name}...",
        "movie_method": "Movie URL",
        "portrait_image": image_url,
        "tags": "design,graphics",
        "status": "publish"
    }
    save_tool_as_csv(data_for_csv)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate TechCEO content generation.")
    parser.add_argument("name", type=str, nargs="?", help="The name of the tool.")
    parser.add_argument("url", type=str, nargs="?", help="The URL of the tool's website.")
    parser.add_argument("--contributor", type=str, default="AIC Community", help="The contributor's name (optional).")
    parser.add_argument("--tools_file", type=str, help="Path to tools.md file containing tool names and links.")
    args = parser.parse_args()

    async def process_tool(tool_name, tool_url, contributor, all_rows):
        class Args:
            pass
        tool_args = Args()
        tool_args.name = tool_name
        tool_args.url = tool_url
        tool_args.contributor = contributor
        
        scraped_text, scraped_html = await scrape_website(tool_url)
        genre = get_genre_with_gemini(scraped_text)
        image_url = find_image_url(scraped_html, tool_url)
        if not image_url:
            image_url = get_google_image(tool_name)
        video_url = find_youtube_video(tool_name)
        trending_questions = get_trending_questions(tool_name)
        generated_content = generate_content_with_gemini(
            scraped_text, tool_name, tool_url, contributor, PLAN_TEMPLATE, image_url, video_url, trending_questions
        )
        generated_content = convert_links(generated_content)
        data_for_csv = {
            "tool_name": tool_name,
            "contributor": contributor,
            "category": genre,
            "generated_content": generated_content,
            "image_url": image_url,
            "video_url": video_url,
            "tool_url": tool_url,
            "excerpt": f"A quick look at {tool_name}...",
            "movie_method": "Movie URL",
            "portrait_image": image_url,
            "tags": "design,graphics",
            "status": "publish"
        }
        all_rows.append(data_for_csv)

    if args.tools_file:
        headers = [
            "Title","Author","Excerpt","Thumbnail","Language","Genres","Tags","Portrait Image","Movie Method","Movie URL","Content","Status"
        ]
        output_file = os.path.join(CSV_OUTPUT_DIR, "all_tools.csv")
        all_rows = []
        with open(args.tools_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"Found {len(lines)} lines in {args.tools_file}")
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
            else:
                parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 2:
                tool_name, tool_url = parts[0], parts[1]
                contributor = args.contributor
                print(f"Processing line {i+1}: {line.strip()}")
                if os.name == 'nt':
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                asyncio.run(process_tool(tool_name, tool_url, contributor, all_rows))
                print(f"Number of rows in all_rows: {len(all_rows)}")
                time.sleep(10) # Add a 10-second delay between requests
        print(f"Finished processing. Total rows to write: {len(all_rows)}")
        # Write all rows to one CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_ALL, delimiter=',')
            writer.writeheader()
            for row in all_rows:
                # Convert to correct row format
                out_row = {h: "" for h in headers}
                out_row["Title"] = row.get("tool_name", "")
                out_row["Author"] = row.get("contributor", "")
                out_row["Excerpt"] = row.get("excerpt", "")
                out_row["Thumbnail"] = row.get("image_url", "")
                out_row["Language"] = row.get("language", "en")
                out_row["Genres"] = row.get("category", "")
                out_row["Tags"] = row.get("tags", "")
                out_row["Portrait Image"] = row.get("portrait_image", "")
                out_row["Movie Method"] = row.get("movie_method", "Movie URL")
                out_row["Movie URL"] = row.get("video_url", "")
                out_row["Content"] = row.get("generated_content", "")
                out_row["Status"] = row.get("status", "publish")
                writer.writerow(out_row)
        print(f"Successfully created batch CSV: {output_file}")
    elif args.name and args.url:
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main(args))
    else:
        print("Please provide either a tool name and URL, or --tools_file with a list of tools.")