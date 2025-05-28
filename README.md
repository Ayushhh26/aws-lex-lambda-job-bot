# Rutgers Job Bot

## Project Overview
This project is an Amazon Lex chatbot designed to help users find the latest job openings at Rutgers University by scraping the official Rutgers job postings website.

## Architecture
The bot's functionality is split between two main AWS services:
- **Amazon Lex:** Handles natural language understanding (NLU), managing the conversation flow, and defining intents (user's goals).
- **AWS Lambda:** Provides the backend code (Python) that is invoked by Lex. This Lambda function performs the web scraping of the Rutgers job board and formats the job listings to be sent back to the user.

## Features
- **Greetings:** Responds to common greetings.
- **Job Search:** Fetches and displays the latest job openings from `https://jobs.rutgers.edu/`.
- **Farewells:** Provides a polite closing message.

## Setup Guide

### Prerequisites
- An AWS Account
- Basic understanding of AWS Lex and Lambda
- Python 3.9+ environment for local development (optional, but good for testing)

### AWS Lambda Setup
1.  **Create a Lambda Function:**
    - Go to the AWS Lambda console.
    - Create a new function from scratch.
    - **Function name:** `RutgersJobsBotLambda`
    - **Runtime:** Python 3.9 (or newer compatible version)
    - **Architecture:** `x86_64`
    - **Permissions:** Create a new role with basic Lambda permissions (this will grant `CloudWatchLogs` access).
2.  **Upload Code & Dependencies:**
    - Create a local folder for your Lambda code (e.g., `rutgers_lambda_code`).
    - Place `lambda_function.py` and `requirements.txt` (provided in this repository) inside this folder.
    - Install dependencies locally into the folder:
        ```bash
        pip install -r requirements.txt -t .
        ```
    - Zip the entire contents of the `rutgers_lambda_code` folder (ensure `lambda_function.py` and the `requests`, `bs4` folders are at the root of the zip).
    - Upload this zip file to your Lambda function in the AWS console.
3.  **Configure Lambda Timeout:**
    - In the Lambda function's configuration, increase the timeout (e.g., to 30 seconds) to allow enough time for web scraping.
4.  **Add Lex Trigger:**
    - In the Lambda function's "Designer" section, add an "Amazon Lex" trigger.
    - Select your `RutgersJobsBot` and ensure it's linked correctly.

### Amazon Lex Bot Setup
1.  **Create a Bot:**
    - Go to the Amazon Lex console.
    - Click "Create bot".
    - **Crucially, select "Traditional"** as the Creation method.
    - **Bot name:** `RutgersJobsBot`
    - **IAM permissions:** Create a role with basic Amazon Lex permissions.
    - **COPPA:** No.
    - Select "Create a blank bot."
2.  **Define Intents:**
    - **GetWelcomeMessage:**
        - **Sample utterances:** `Hello`, `Hi`, `Greetings`, `Start`, `Welcome`
        - **Initial response:** `Hello! Welcome to Rutgers University. I'm your virtual campus guide. How can I assist you today regarding Rutgers job openings?`
    - **GetRutgersJobOpenings:**
        - **Sample utterances:** `What are the latest job openings?`, `Show me Rutgers jobs.`, `Are there any jobs available?`, `Find me a job at Rutgers.`, `Recent job listings.`, `Tell me about new positions.`, `What jobs are posted?`, `List current vacancies.`
        - **Fulfillment:** Enable "Use a Lambda function for fulfillment" and select `RutgersJobsBotLambda`. Grant permissions if prompted.
    - **SayGoodbye:**
        - **Sample utterances:** `Goodbye`, `Bye`, `See you later`, `Thanks, bye`, `I'm done`
        - **Closing response:** `You're welcome! I hope you consider joining the Rutgers community. Goodbye!`
3.  **Build the Bot:**
    - After configuring all intents, click the "Build" button in the top right corner of the Lex console.

## How to Use
Once the bot is built, you can test it directly in the Amazon Lex console's "Test bot" panel:
- Type "Hi" to get a welcome message.
- Type "What are the latest job openings?" to retrieve job listings.
- Type "Goodbye" to end the conversation.

## Code Details (lambda_function.py)
- The `scrape_rutgers_jobs` function handles the web scraping logic.
- It uses `requests` to fetch the HTML content and `BeautifulSoup` to parse it.
- Selectors are specifically tuned to the HTML structure of `https://jobs.rutgers.edu/`.
- The `lambda_handler` function processes Lex events and constructs the response message.

## Future Improvements
- Add filtering capabilities (e.g., jobs by department, campus).
- Implement error handling for no jobs found for specific filters.
- Use more advanced Lex features like slots for dynamic queries.
- Deploy the bot to a channel like Facebook Messenger or Slack.