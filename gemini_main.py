import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
import csv
from playwright.async_api import async_playwright
import argparse
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from urllib.parse import urljoin

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
CSV_OUTPUT_DIR = "output_csv"
HTML_OUTPUT_DIR = "output_html_gemini"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# --- Main Application Logic ---

async def scrape_website(url: str) -> tuple[str, str]:
    """
    Asynchronously scrapes the text and HTML content of a given URL.
    Returns a tuple of (text_content, html_content).
    """
    print(f"Scraping {url}...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
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
            q=f"{tool_name} tutorial explainer",
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


def generate_content_with_gemini(scraped_text: str, tool_name: str, tool_url: str, contributor: str, plan_template: str, image_url: str, video_url: str) -> str:
    """
    Generates content using Google's Gemini model based on a template and scraped text.
    """
    print("Generating content with Gemini...")
    genai.configure(api_key=GEMINI_API_KEY)
    
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are a content creator for a tech blog. Your task is to create a blog post about a new tool, meticulously following the provided template's structure and formatting. Your writing style should be simple, accessible, and engaging, as if you're explaining the tool to a friend who is new to the tech space. Avoid jargon wherever possible.

    **CRITICAL INSTRUCTIONS:**
    1.  **PRESERVE ALL HTML AND SPACING:** Your response must replicate the exact HTML structure of the template, including all `<p>` tags, `<hr />` tags, and newlines to ensure proper spacing between sections.
    2.  **NO PLACEHOLDERS:** You must write out the full text for all sections. Do NOT use placeholders like "[Same as the original template's Stay Safe section]". Generate the complete content for every field.
    3.  **START IMMEDIATELY:** The response must begin *directly* with "📘 Tool Name:", with no preceding text.
    4.  **NO CODE BLOCKS:** Do not wrap your response in markdown code fences like ```html or ```.
    5.  **NUMBERED LISTS:** All lists (like under Pros, Cons, etc.) MUST be numbered (e.g., 1., 2., 3.).
    6.  **CLICKABLE LINKS:** All links MUST be formatted as `<a href="URL">TEXT</a>`.
    7.  **USE PROVIDED LINKS:** You MUST use the provided Image URL and Video URL in the final output. If a URL is empty, state that a suitable one could not be found.

    **Template:**
    {plan_template}

    **Tool Information:**
    - Tool Name: {tool_name}
    - Tool URL: {tool_url}
    - Contributor: {contributor}
    - Image URL: {image_url}
    - Video URL: {video_url}
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

def save_tool_as_csv_from_template(data: dict):
    """
    Creates a new CSV for a tool by filling in a template file.
    """
    if not os.path.exists(CSV_OUTPUT_DIR):
        os.makedirs(CSV_OUTPUT_DIR)

    tool_name = data.get("tool_name", "untitled")
    file_name = tool_name.replace(' ', '_').lower()
    file_path = os.path.join(CSV_OUTPUT_DIR, f"{file_name}_post.csv")

    try:
        with open('test.csv', 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        print("Error: test.csv template not found.")
        return

    # Replace placeholders in the template
    output_content = template_content.replace('[TOOL_NAME]', tool_name)
    output_content = output_content.replace('[AUTHOR]', data.get("contributor", ""))
    output_content = output_content.replace('[CONTENT_HERE]', data.get("generated_content", ""))

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(output_content)
        
    print(f"Successfully created CSV from template: {file_path}")


async def main(args):
    """
    Main function to run the automation.
    """
    plan_template = r'''
    📘 Tool Name: [tool name]
    🔗 Official Site: [url]
    🎥 Explainer Video: [youtube video link]
    🧑‍💻 AIC Contributor: AIC Community


    🧩 Quick Look: [Simple breakdown - keep it to under 7 words]
    Beginner Benefit: [Simple breakdown - keep it to under 7 words]

    🌟 Nansen 101:
    [explainer 101 section - give brief breakdown. 2-3 paragraphs]

    📚 Key AI Concepts Explained:
    [list 3 bullet points of different concepts to consider when using this tool. Make each bullet point
    a single sentence (1-2 sentences)]

    📖 Words to Know:
    [list 3 bullet points of different words to know when using this tool. Make each bullet point a
    single sentence (8-12 words)]

    🎯 Imagine This: [give an analogy that a normal person would understand 1-2 sentences.]

    🌟 Fun Fact About the Tool: [Provide a surprising or little-known fun fact about the tool, its history, or its creators. 1-3 sentences.]

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

    ❓ Beginner FAQ:
    ● [3 bullet points of beginner FAQ. 3-5 word question. Then 1 sentence answer (8-12 words)]

    🚀 Getting Started:
    1. [3-6 numbered steps on how to get started. 1 sentence per step (8-12 words). Include
    affiliate link and steps users have to do to sign up]

    💡 Power-Ups:
    ● [3 bullet points for more advanced users. 1-2 sentence answer (15-20 words per
    sentence)]

    🎯 Difficulty Score: 2/10 🟢 (Super Easy)
    [2 paragraphs. Provide a ranking score for someone new to using this. 1 being super easy, 10 being advanced expert. Rank usability, enjoyment, benefits of use, skills needed to use this, benefit and negative. Do not make false claims on anything throughout the content]

    ⭐ Official AI-Driven Rating: 8.6/10
    [2 paragraphs. Provide a ranking score for someone new to using this. 1 being super easy, 10 being advanced expert. Give your unbiased opinion. Do not make false claims on anything throughout the content. Mention why you like it. Show points awarded and deducted to prove why you gave this score.]

    ⚖️ Stay Safe: The tools and information on this site are aggregated from community contributions and internet sources. We strongly recommend users independently verify all details, consult original resources for accuracy, and exercise caution. The information, including company profiles, pricing, rules, and structures, is based on current knowledge as of 12:55 PM EDT on Friday, August 22, 2025, and is subject to change at the discretion of the respective entities. This site is provided "as-is" with no warranties, and no professional, financial, or legal advice is offered or implied. We disclaim all liability for errors, omissions, damages, or losses arising from the use of this information.
    This platform is intended to showcase tools for informational purposes only and does not endorse or advise on financial investments or decisions. Users must conduct their own due diligence (DYOR), verify the authenticity of tool websites to avoid phishing scams, and secure accounts with strong passwords and two-factor authentication. AIC is not responsible for the performance, safety, outcomes, or risks associated with any listed tools. Some links on this site may be affiliate links, meaning we may earn a commission if you click and make a purchase, at no additional cost to you. Always research thoroughly, comply with local laws and regulations, and consult qualified financial or legal professionals before taking action to understand potential risks. Nothing herein constitutes professional advice, and all decisions are at the user’s sole discretion. This disclaimer is governed by the laws of St. Petersburg, Florida, USA.
    '''

    scraped_text, scraped_html = await scrape_website(args.url)
    if not scraped_text:
        return

    image_url = find_image_url(scraped_html, args.url)
    video_url = find_youtube_video(args.name)

    generated_content = generate_content_with_gemini(
        scraped_text, args.name, args.url, args.contributor, plan_template, image_url, video_url
    )
    if not generated_content:
        return
        
    save_as_html(generated_content, args.name)

    data_for_csv = {
        "tool_name": args.name,
        "contributor": args.contributor,
        "category": args.category,
        "generated_content": generated_content
    }
    save_tool_as_csv_from_template(data_for_csv)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate TechCEO content generation.")
    parser.add_argument("name", type=str, help="The name of the tool.")
    parser.add_argument("url", type=str, help="The URL of the tool's website.")
    parser.add_argument("--contributor", type=str, default="TechCEO", help="The contributor's name (optional).")
    parser.add_argument("--category", type=str, default="AI", help="The category of the tool (e.g., AI, Crypto).")
    
    args = parser.parse_args()

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(args))
