import json
import logging
import os
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

CAMPUS_IDS = {
    "new brunswick": "3",
    "newark": "1",
    "camden": "2",
}

def get_campus_id(campus_name):
    return CAMPUS_IDS.get(campus_name.lower())

def scrape_rutgers_jobs(campus_id=None, keyword=None):
    base_url = "https://jobs.rutgers.edu/postings/search"
    
    params = {
        "utf8": "✓",
        "query": keyword if keyword else "", 
        "query_v0_posted_at_date": "",
        "435": "",
        "225": "",
        "commit": "Search"
    }

    if campus_id:
        params["2201[]"] = campus_id 
    else:
        params.pop("2201[]", None)
            
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    encoded_params = urllib.parse.urlencode(params)
    logger.info(f"Requesting URL: {base_url}?{encoded_params}")

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        return None

    logger.debug(f"--- RAW HTML RESPONSE (first 2000 chars, if available) ---\n{response.text[:2000]}\n--- END RAW HTML RESPONSE ---")

    soup = BeautifulSoup(response.content, 'html.parser')
    
    job_listings_raw = soup.select('div#search_results div.job-item.job-item-posting') 
    
    logger.info(f"Number of raw job_listings found by BeautifulSoup (after new selector): {len(job_listings_raw)}")

    jobs = []
 

    for job_item in job_listings_raw: # Iterate over all raw listings
        title_tag = job_item.select_one('div.job-title.col-md-4 h3 a')
        title = title_tag.get_text(strip=True) if title_tag else "Untitled Job"
        link = "https://jobs.rutgers.edu" + title_tag['href'] if title_tag and 'href' in title_tag.attrs else "#"

        department_campus_divs = job_item.select('div.col-md-8 div.tbody-cell.col-6')
        department_campus_parts = []
        for div in department_campus_divs:
            text = div.get_text(strip=True)
            if not re.fullmatch(r'(\d{2}[A-Z]{2}\d{4}|\d+)', text): 
                if text:
                    department_campus_parts.append(text)
        department_campus = ", ".join(department_campus_parts) if department_campus_parts else "N/A"

        job_data = {
            'title': title,
            'department_campus': department_campus,
            'link': link
        }

        print(f"Scraped job (raw): Title='{job_data.get('title')}', Dept/Campus='{job_data.get('department_campus')}'")

       
    
        jobs.append(job_data)

    # Update log message
    if keyword: # If a keyword was provided to the function (meaning the website should have filtered)
        logger.info(f"Returning {len(jobs)} jobs based on website's keyword filter for '{keyword}'")
    else: # If no keyword was provided, it's a general campus search
        logger.info(f"Returning {len(jobs)} jobs for general search in '{get_campus_id(campus_id)}'")
    
    return jobs


def lambda_handler(event, context):
    logger.debug(f"Raw event: {json.dumps(event, indent=2)}")

    response = {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": event['sessionState']['intent']['name'],
                "state": "Fulfilled"
            }
        },
        "messages": []
    }

    slots = event['sessionState']['intent']['slots']
    logger.debug(f"DEBUG: Raw slots object: {slots}")

    campus_slot = slots.get('campus')
    logger.debug(f"DEBUG: Raw campus_slot: {campus_slot}")

    keyword_slot = slots.get('keyword')
    logger.debug(f"DEBUG: Raw keyword_slot: {keyword_slot}")

    campus_filter = None
    if campus_slot and campus_slot['value']:
        campus_filter = campus_slot['value']['interpretedValue']
        logger.info(f"User requested campus filter: {campus_filter}")

    keyword_filter = None
    if keyword_slot and keyword_slot['value']:
        keyword_filter = keyword_slot['value']['interpretedValue']
        logger.info(f"User requested keyword filter (from interpretedValue): {keyword_filter}")
    logger.debug(f"DEBUG: Final keyword_filter value: {keyword_filter}")

    if not campus_filter:
        response['sessionState']['dialogAction']['type'] = 'Delegate'
        response['sessionState']['intent']['state'] = 'InProgress'
        response['messages'].append({
            "contentType": "PlainText",
            "content": "Which campus are you interested in (e.g., New Brunswick, Newark, Camden)?"
        })
        return response

    campus_id = get_campus_id(campus_filter)

    if not campus_id:
        response['messages'].append({
            "contentType": "PlainText",
            "content": f"I don't recognize '{campus_filter}' as a valid Rutgers campus. Please try a valid campus like New Brunswick, Newark, or Camden."
        })
        return response
    
    logger.info(f"Applying campus filter for {campus_filter} with ID {campus_id}")

    try:
        if keyword_filter:
            logger.info(f"Sending keyword to site: {keyword_filter}")
            jobs = scrape_rutgers_jobs(campus_id=campus_id, keyword=keyword_filter)
        else:
            jobs = scrape_rutgers_jobs(campus_id=campus_id)

        if jobs:
            job_messages = []
            for i, job in enumerate(jobs[:5]): # Limit to top 5 results
                job_messages.append(f"* {job['title']} ({job['department_campus']}) - {job['link']}")
            
            job_list_text = "\n".join(job_messages)
            response['messages'].append({
                "contentType": "PlainText",
                "content": f"Here are some of the latest Rutgers job openings in '{campus_filter}':\n{job_list_text}\nYou can visit https://jobs.rutgers.edu/ for more details."
            })
        else:
            if keyword_filter:
                response['messages'].append({
                    "contentType": "PlainText",
                    "content": f"I couldn't find any job openings for '{keyword_filter}' in '{campus_filter}' at Rutgers at the moment. Please try a different keyword/campus or search later."
                })
            else:
                response['messages'].append({
                    "contentType": "PlainText",
                    "content": f"I couldn't find any job openings in '{campus_filter}' at Rutgers at the moment. Please try again later or check the official website."
                })

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        response['messages'].append({
            "contentType": "PlainText",
            "content": "I'm sorry, I'm having trouble connecting to the job site right now. Please try again later."
        })
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        response['messages'].append({
            "contentType": "PlainText",
            "content": "An unexpected error occurred while fetching job openings. Please try again later."
        })

    return response