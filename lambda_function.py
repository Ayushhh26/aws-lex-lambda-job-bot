import json
import requests
from bs4 import BeautifulSoup
import re 

def lambda_handler(event, context):
    try:
        # Lex V2 event structure for intent fulfillment
        if event['sessionState']['intent']['name'] == 'GetRutgersJobOpenings':
            jobs_data = scrape_rutgers_jobs()
            if jobs_data:
                response_message = "Here are some of the latest Rutgers job openings:\n\n" 
                
                for job in jobs_data[:5]: # Take only the first 5 jobs
                    # Construct a more robust string with default values
                    title = job.get('title', 'N/A')
                    department_campus = job.get('department_campus', 'N/A')
                    link = job.get('link', '#') # Use '#' as a placeholder for missing links

                    
                    response_message += f"* {title} ({department_campus}) - {link}\n" # Added bullet point and newline
                response_message += "\nYou can visit https://jobs.rutgers.edu/ for more details."
            else:
                response_message = "I couldn't find any job openings at Rutgers at the moment. Please try again later."

            return {
                'sessionState': {
                    'dialogAction': {
                        'type': 'Close'
                    },
                    'intent': {
                        'name': 'GetRutgersJobOpenings',
                        'state': 'Fulfilled'
                    }
                },
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': response_message
                    }
                ]
            }

        # Add other intents if necessary (e.g., GetWelcomeMessage, SayGoodbye)
        elif event['sessionState']['intent']['name'] == 'GetWelcomeMessage':
            return {
                'sessionState': {
                    'dialogAction': {
                        'type': 'Close'
                    },
                    'intent': {
                        'name': 'GetWelcomeMessage',
                        'state': 'Fulfilled'
                    }
                },
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': 'Hello! Welcome to Rutgers University. I\'m your virtual campus guide. How can I assist you today regarding Rutgers job openings?'
                    }
                ]
            }
        elif event['sessionState']['intent']['name'] == 'SayGoodbye':
            return {
                'sessionState': {
                    'dialogAction': {
                        'type': 'Close'
                    },
                    'intent': {
                        'name': 'SayGoodbye',
                        'state': 'Fulfilled'
                    }
                },
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': 'You\'re welcome! I hope you consider joining the Rutgers community. Goodbye!'
                    }
                ]
            }
        else:
            return {
                'sessionState': {
                    'dialogAction': {
                        'type': 'Close'
                    },
                    'intent': {
                        'name': event['sessionState']['intent']['name'],
                        'state': 'Fulfilled'
                    }
                },
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': "I'm sorry, I don't understand that request."
                    }
                ]
            }

    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': event['sessionState']['intent']['name'],
                    'state': 'Failed'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': "An error occurred while trying to fetch job openings. Please try again later."
                }
            ]
        }

def scrape_rutgers_jobs():
    url = "https://jobs.rutgers.edu/postings/search?sort=435+asc" # Sort by latest
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, 'html.parser')

        # Updated selector for individual job listings
        job_listings = soup.select('div#search_results div.job-item.job-item-posting')

        jobs = []
        for job_item in job_listings: 
            # Extract Title and Link
            title_tag = job_item.select_one('div.job-title.col-md-4 h3 a')
            title = title_tag.get_text(strip=True) if title_tag else "Untitled Job"
            link = "https://jobs.rutgers.edu" + title_tag['href'] if title_tag and 'href' in title_tag.attrs else "#"

            # Extract Department/Campus
            department_campus_divs = job_item.select('div.col-md-8 div')
            department_campus = "N/A" # Default

            if department_campus_divs:
                relevant_texts = []
                for div in department_campus_divs:
                    text = div.get_text(strip=True)
                    # Exclude text that looks like job IDs (e.g., 23FA0824, 25FA0092)
                    if not re.fullmatch(r'\d{2}[A-Z]{2}\d{4}', text) and not text.isdigit():
                        if text: # Ensure it's not empty
                            relevant_texts.append(text)

                if relevant_texts:
                    # Join them, e.g., "CINJ-Finance, Rutgers Biomedical and Health Sciences (RBHS)"
                    department_campus = ", ".join(relevant_texts)
                else:
                    department_campus = "N/A" # If no relevant text found

            jobs.append({
                'title': title,
                'department_campus': department_campus,
                'link': link
            })
        return jobs

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Scraping error: {e}")
        return None