# TechCEO AI/Crypto Tool Content Automator

This project automates the creation of WordPress blog posts about AI and Crypto tools. It uses a Python script powered by Google's Gemini AI to scrape a tool's website, generate high-quality content based on a predefined template, and format it into a WordPress-compatible CSV file for easy uploading.

## Features

- **Web Scraping:** Uses Playwright to scrape the content of any tool's URL.
- **AI Content Generation:** Leverages the Gemini 1.5 Flash model to generate detailed and well-structured content.
- **Template-Based:** The entire blog post structure is controlled by a clean, easy-to-edit template (`plan.md`).
- **WordPress-Compatible CSV:** The script generates a CSV file (`_post.csv`) for each tool that is formatted to be uploaded directly using the WordPress importer.

---

## Project Structure

```
.
├── .env                  # Stores the API key for the Gemini AI model.
├── deploy.md             # Guide with different options for deploying the script.
├── gemini_main.py        # The main Python script that runs the automation.
├── plan.md               # The master template for the AI-generated content.
├── requirements.txt      # A list of all the Python libraries needed for the project.
├── test.csv              # A simple, working template for the final CSV output.
└── tool_submission_form.html # A modern HTML form for users to submit new tools.
```

---

## Setup Instructions

Follow these steps to get the project running on your local machine.

### 1. Python Environment

It is highly recommended to use a Python virtual environment to keep the project's dependencies isolated from your system.

```bash
# Create a new virtual environment in a folder named .venv
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

### 2. Install Dependencies

Install all the required Python libraries using the `requirements.txt` file.

```bash
# Install all libraries
pip install -r requirements.txt

# Download the necessary browsers for Playwright
playwright install
```

### 3. Set Up API Key

The script needs a Google Gemini API key to generate content.

1.  Create a file named `.env` in the main project directory.
2.  Add your API key to the file like this:

    ```
    GEMINI_API_KEY=your_google_api_key_here
    ```

---

## How to Run the Script

The script is now run from the command line, passing the tool's information as arguments.

### Basic Usage

Provide the tool's name and URL as arguments.

```bash
python gemini_main.py "Canva" "https://www.canva.com"
```

### Optional Arguments

You can also specify a contributor and a category.

```bash
python gemini_main.py "Goose AI" "https://block.github.io/goose/" --contributor "Community" --category "AI"
```

### Help

To see all available options, use the `-h` or `--help` flag.

```bash
python gemini_main.py -h
```

After running, the script will create a new directory named `output_csv`. Inside, you will find a new file (e.g., `canva_post.csv`) that is ready to be uploaded to WordPress.

---

## Deployment

For information on how to deploy this script to a server so it can be triggered by a webhook, please see the detailed guide in `deploy.md`.

## WordPress Submission Form

The `tool_submission_form.html` file contains a modern, dark-themed HTML form that you can use on your WordPress site.

-   **To Use:** Edit the file and replace the placeholder `https://your-webhook-url.com/endpoint` with your actual webhook URL.
-   **To Embed:** Copy the entire content of the file and paste it into a "Custom HTML" block on any WordPress page or post.
