import json
import requests
from bs4 import BeautifulSoup
import re

def lambda_handler(event, context):
    try:
        intent_name = event['sessionState']['intent']['name']
        
        if intent_name == 'GetRutgersJobOpenings':
            slots = event['sessionState']['intent']['slots']
            campus_slot = slots.get('campus')
            keyword_slot = slots.get('keyword') # Ensure this matches your slot name in Lex if it's 'jobKeyword'

            campus_filter = None
            keyword_filter = None

            if campus_slot and campus_slot.get('value') and campus_slot['value'].get('interpretedValue'):
                campus_filter = campus_slot['value']['interpretedValue']
                print(f"User requested campus filter: {campus_filter}")

            if keyword_slot and keyword_slot.get('value') and keyword_slot['value'].get('interpretedValue'):
                keyword_filter = keyword_slot['value']['interpretedValue']
                print(f"User requested keyword filter: {keyword_filter}")

            # Pass both campus_filter and keyword_filter to your scraping function
            jobs_data = scrape_rutgers_jobs(campus=campus_filter, keyword=keyword_filter)

            if jobs_data:
                response_message = "Here are some of the latest Rutgers job openings"
                if keyword_filter:
                    response_message += f" for '{keyword_filter}'"
                if campus_filter:
                    response_message += f" in '{campus_filter}'"
                response_message += ":\n"
                for job in jobs_data[:5]:  # Limit to 5 for brevity
                    title = job.get('title', 'N/A')
                    department_campus = job.get('department_campus', 'N/A')
                    link = job.get('link', '#')
                    response_message += f"\n* {title} ({department_campus}) - {link}"
                response_message += "\n\nYou can visit https://jobs.rutgers.edu/ for more details."
            else:
                if keyword_filter and campus_filter:
                    response_message = f"I couldn't find any job openings for '{keyword_filter}' in '{campus_filter}' at Rutgers at the moment. Please try a different keyword/campus or search later."
                elif keyword_filter:
                    response_message = f"I couldn't find any job openings for '{keyword_filter}' at Rutgers at the moment. Please try a different keyword or search later."
                elif campus_filter:
                    response_message = f"I couldn't find any job openings for '{campus_filter}' at Rutgers at the moment. Please try a different campus or search later."
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

        elif intent_name == 'GetWelcomeMessage':
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
                        'content': "Hello! Welcome to Rutgers University. I'm your virtual campus guide. How can I assist you today regarding Rutgers job openings?"
                    }
                ]
            }
        elif intent_name == 'SayGoodbye':
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
                        'content': "You're welcome! I hope you consider joining the Rutgers community. Goodbye!"
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
                        'name': intent_name,
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

def scrape_rutgers_jobs(campus=None, keyword=None):
    campus_ids = {
        "New Brunswick": "3",
        "Newark": "1",
        "Camden": "2"
    }

    base_url = "https://jobs.rutgers.edu/postings/search"
    params = {"sort": "435 asc"}  # Default sort by latest

    if campus and campus in campus_ids:
        params["2201[]"] = campus_ids[campus]
        print(f"Applying campus filter for {campus} with ID {campus_ids[campus]}")

    if keyword:
        params["query"] = keyword
        print(f"Applying keyword filter: {keyword}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        job_listings = soup.select('div#search_results div.job-item.job-item-posting')

        jobs = []
        for job_item in job_listings:
            title_tag = job_item.select_one('div.job-title.col-md-4 h3 a')
            title = title_tag.get_text(strip=True) if title_tag else "Untitled Job"
            link = "https://jobs.rutgers.edu" + title_tag['href'] if title_tag and 'href' in title_tag.attrs else "#"

            department_campus_divs = job_item.select('div.col-md-8 div')
            department_campus = "N/A"

            print(f"--- Processing Job: {title} ---") # Added for debugging
            extracted_texts = [] # Added for debugging

            if department_campus_divs:
                relevant_texts = []
                for i, div in enumerate(department_campus_divs): # Added enumerate
                    text = div.get_text(strip=True)
                    extracted_texts.append(f"Div {i}: '{text}'") # Added for debugging
                    if not re.fullmatch(r'\d{2}[A-Z]{2}\d{4}', text) and not text.isdigit():
                        if text:
                            relevant_texts.append(text)
                if relevant_texts:
                    department_campus = ", ".join(relevant_texts)
                else:
                    department_campus = "N/A"
            print(f"Raw extracted texts for department/campus: {extracted_texts}") # Added for debugging
            print(f"Final department_campus value: {department_campus}") # Added for debugging

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