import os
import json
import asyncio
import requests
from pyppeteer import launch
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from openai import OpenAI
from app.prompts import get_analysis_prompt, get_faq_prompt
from fake_useragent import UserAgent
import random
import time
from app.logger import setup_logger, save_data_with_rotation
import re
from datetime import datetime
import json_repair
import nest_asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from app.status_store import set_status
from app.translate_text import translate_large_text_if_japanese, translate_data_to_japanese
from app.university_prompts import (
    get_university_general_prompt,
    get_university_specialized_prompt,
    UNIVERSITY_AGENT_TYPES,
)

# Initialize logger
logger = setup_logger('utils')

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Constants
MAX_CONTENT_LENGTH = 80000  # Maximum content length in characters
PYPPETEER_EXECUTOR = ProcessPoolExecutor(max_workers=1)  # Single worker for Pyppeteer

def _fetch_with_pyppeteer_process(url):
    """
    Run Pyppeteer in a separate process
    """
    async def _fetch_html():
        browser = None
        try:
            browser = await launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu'
                ]
            )
            page = await browser.newPage()
            await page.setViewport({'width': 1280, 'height': 800})
            await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 30000})
            content = await page.content()
            return content
        except Exception as e:
            print(f"Error in Pyppeteer fetch: {str(e)}")  # Use print for process logging
            return None
        finally:
            if browser:
                try:
                    await browser.close()
                except:
                    pass
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_fetch_html())
        loop.close()
        return result
    except Exception as e:
        print(f"Error in Pyppeteer process: {str(e)}")  # Use print for process logging
        return None

def run_pyppeteer(url):
    """
    Run Pyppeteer in a separate process
    """
    try:
        # Run Pyppeteer in a separate process
        future = PYPPETEER_EXECUTOR.submit(_fetch_with_pyppeteer_process, url)
        return future.result(timeout=60)  # 60 second timeout
    except Exception as e:
        logger.error(f"Error running Pyppeteer: {str(e)}")
        return None

def sanitize_filename(url):
    """
    Convert URL to a valid filename
    """
    # Remove protocol and www
    filename = re.sub(r'^https?://(www\.)?', '', url)
    # Replace invalid characters with underscore
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    # Remove trailing slashes
    filename = filename.rstrip('/')
    return filename

def get_openai_client():
    """
    Initialize and return OpenAI client
    """
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        logger.debug("OpenAI client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        raise

def get_random_headers():
    """
    Generate random headers for each request
    """
    try:
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        logger.debug(f"Generated random headers with User-Agent: {headers['User-Agent']}")
        return headers
    except Exception as e:
        logger.warning(f"Failed to generate random headers, using fallback: {str(e)}")
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

def is_valid_url(url):
    """
    Check if the URL is valid and belongs to the same domain
    """
    try:
        result = urlparse(url)
        is_valid = all([result.scheme, result.netloc])
        
        # Remove 'www.' from the domain for comparison
        domain = result.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
            
        logger.debug(f"URL validation for {url}: {is_valid}, domain: {domain}")
        return is_valid
    except Exception as e:
        logger.error(f"URL validation failed for {url}: {str(e)}")
        return False

def extract_structured_content(soup, url):
    """
    Extract structured content from the page and translate if Japanese
    """
    try:
        # Initialize content structure
        content_parts = []
        # Extract title
        title = soup.title.string if soup.title else ""
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'] if meta_desc else ""
        # Extract main content in sequence
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'li', 'span']):
            if element.name in ['ul', 'ol']:
                # Skip the list container itself, we'll get its items
                continue
            # Get text content
            text = element.get_text(strip=True)
            if text:
                # Add element type as prefix for better context
                element_type = element.name.upper()
                content_parts.append(f"{element_type}: {text}")
        # Combine all content with newlines
        content = translate_large_text_if_japanese('\n'.join(filter(None, content_parts)))  
        # Create structured data
        structured_data = {
            "url": url,
            "title": title,
            "description": description,
            "content": content
        }
        logger.debug(f"Extracted structured content from {url}")
        return structured_data
        
    except Exception as e:
        logger.error(f"Error extracting structured content from {url}: {str(e)}")
        raise

def get_links(soup, base_url):
    """
    Extract all links from the page that belong to the same domain
    """
    try:
        # Parse base URL and get domain without www
        base_parsed = urlparse(base_url)
        base_domain = base_parsed.netloc
        if base_domain.startswith('www.'):
            base_domain = base_domain[4:]
            
        links = set()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            
            # Parse the full URL and get domain without www
            full_parsed = urlparse(full_url)
            full_domain = full_parsed.netloc
            if full_domain.startswith('www.'):
                full_domain = full_domain[4:]
            
            if is_valid_url(full_url) and full_domain == base_domain:
                links.add(full_url)
        
        logger.debug(f"Found {len(links)} valid links on {base_url}")
        return links
    except Exception as e:
        logger.error(f"Failed to extract links from {base_url}: {str(e)}")
        return set()

def is_content_sufficient(soup):
    """
    Check if the scraped content is sufficient
    Returns True if content seems valid, False if it might need JavaScript rendering
    """
    # Check for common indicators of insufficient content
    if not soup.title:
        return False
    # Check if main content elements exist
    main_content = soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'li', 'span'])
    if len(main_content) < 3:  # If we have very few content elements
        return False
    # Check for common JavaScript-rendered content patterns
    if soup.find('div', {'id': 'root'}) and not soup.find('div', {'id': 'root'}).get_text(strip=True):
        return False
    return True

def prioritize_links(links):
    priority_keywords = ['price', 'pricing', 'cost', 'plans', 'subscription']
    prioritized = []
    others = []
    for link in links:
        if any(keyword in link.lower() for keyword in priority_keywords):
            prioritized.append(link)
        else:
            others.append(link)
    # Prioritize links with keywords by putting them first
    return prioritized + others

def trim_content(content, max_length):
    """
    Trim content to fit within max_length while preserving structure
    """
    if len(content) <= max_length:
        return content
        
    # Split content into lines to preserve structure
    lines = content.split('\n')
    trimmed_lines = []
    current_length = 0
    
    for line in lines:
        if current_length + len(line) + 1 <= max_length:  # +1 for newline
            trimmed_lines.append(line)
            current_length += len(line) + 1
        else:
            # If we can't fit the whole line, try to fit part of it
            remaining_length = max_length - current_length
            if remaining_length > 20:  # Only add partial line if we have enough space
                trimmed_lines.append(line[:remaining_length] + "...")
            break
    
    return '\n'.join(trimmed_lines)

def scrape_url(url, max_pages=1, task_id=None):
    """
    Scrape content from a given URL and its linked pages up to max_pages
    """
    logger.info(f"Starting scraping process for {url} with max_pages={max_pages}")
    try:
        if task_id:
            set_status(task_id, {"step": "scraping", "progress": 10, "message": "Scraping website content"})
        visited_urls = set()
        urls_to_visit = {url}
        all_content = []
        total_content_length = 0
        
        while urls_to_visit and len(visited_urls) < max_pages:
            current_url = urls_to_visit.pop()
            
            if current_url in visited_urls:
                logger.debug(f"Skipping already visited URL: {current_url}")
                continue
                
            try:
                logger.info(f"Scraping URL: {current_url}")
                headers = get_random_headers()
                
                # Add a small random delay between requests
                delay = random.uniform(1, 3)
                logger.debug(f"Waiting {delay:.2f} seconds before request")
                time.sleep(delay)
                
                # First attempt with regular requests
                try:
                    response = requests.get(current_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Regular request failed for {current_url}, trying Pyppeteer: {str(e)}")
                    html = run_pyppeteer(current_url)
                    if html:
                        soup = BeautifulSoup(html, 'html.parser')
                        logger.info("Successfully fetched content with Pyppeteer")
                    else:
                        logger.warning(f"Both regular request and Pyppeteer failed for {current_url}")
                        continue
                
                # Check if content seems sufficient
                if not is_content_sufficient(soup):
                    logger.info(f"Content seems insufficient, trying Pyppeteer for {current_url}")
                    html = run_pyppeteer(current_url)
                    if html:
                        soup = BeautifulSoup(html, 'html.parser')
                        logger.info("Successfully fetched content with Pyppeteer")
                    else:
                        logger.warning("Pyppeteer fallback failed, using original content")
                
                # Extract structured content
                structured_data = extract_structured_content(soup, current_url)
                current_content_length = len(structured_data['content']) + len(structured_data['description'])
                
                # Only add content if it's not empty
                if structured_data['content'].strip():
                    # If this is the first page and content exceeds MAX_CONTENT_LENGTH, trim it
                    if len(visited_urls) == 0 and current_content_length > MAX_CONTENT_LENGTH:
                        logger.warning(f"First page content exceeds MAX_CONTENT_LENGTH, trimming content")
                        # Calculate how much content we can keep
                        available_length = MAX_CONTENT_LENGTH - len(structured_data['description'])
                        structured_data['content'] = trim_content(structured_data['content'], available_length)
                        current_content_length = len(structured_data['content']) + len(structured_data['description'])
                    
                    # Check if adding this content would exceed the limit for subsequent pages
                    if total_content_length + current_content_length > MAX_CONTENT_LENGTH:
                        logger.warning(f"Content length limit reached ({total_content_length} + {current_content_length} > {MAX_CONTENT_LENGTH}). Skipping remaining pages.")
                        break
                    
                    all_content.append(structured_data)
                    total_content_length += current_content_length
                    visited_urls.add(current_url)
                    # Update progress for each page scraped
                    if task_id:
                        progress = min(10 + int(20 * len(visited_urls) / max_pages), 30)
                        set_status(task_id, {"step": "scraping", "progress": progress, "message": f"Scraped {len(visited_urls)} of {max_pages} pages"})
                else:
                    logger.warning(f"Skipping {current_url} due to empty content")
                
                # Get new links if we haven't reached max_pages
                if len(visited_urls) < max_pages:
                    new_links = get_links(soup, current_url)
                    prioritized_links = prioritize_links(new_links - visited_urls)
                    # Use a list to maintain order, and add prioritized links to the front
                    urls_to_visit = list(prioritized_links) + list(urls_to_visit)
                    urls_to_visit = set(urls_to_visit)  # Convert back to set if you want to avoid duplicates
                    logger.debug(f"Added {len(new_links - visited_urls)} new URLs to visit")
                    
            except Exception as e:
                logger.error(f"Error scraping {current_url}: {str(e)}")
                continue
        
        if not all_content:
            error_msg = f"No content could be scraped from {url}. The website might be blocking automated access or the content is not accessible."
            logger.error(error_msg)
            if task_id:
                set_status(task_id, {"step": "error", "progress": 100, "message": error_msg})
            raise Exception(error_msg)
            
        logger.info(f"Completed scraping {len(visited_urls)} pages, total content length: {total_content_length}")
        if task_id:
            set_status(task_id, {"step": "business_overview", "progress": 33, "message": "Creating business overview"})
        return all_content
        
    except Exception as e:
        logger.error(f"Error in scraping process for {url}: {str(e)}")
        if task_id:
            set_status(task_id, {"step": "error", "progress": 100, "message": str(e)})
        raise Exception(f"Error in scraping process: {str(e)}")

def build_combined_content(content):
    formatted_content = []
    domain = None
    for page in content:
        if not domain:
            parsed_url = urlparse(page['url'])
            domain = parsed_url.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
        formatted_content.append(f"URL: {page['url']}")
        formatted_content.append(f"Title: {page['title']}")
        formatted_content.append(f"Description: {page['description']}")
        formatted_content.append("Content:")
        formatted_content.append(page['content'])
        formatted_content.append("\n---\n")
    return "\n".join(formatted_content), domain

def call_openai(client, prompt, models=None):
    """
    Call OpenAI API with a list of models. Try each model in order until one succeeds.
    Args:
        client: OpenAI client instance
        prompt: The prompt to send
        models: List of model names to try (if None, use default list)
    Returns:
        The content of the first successful completion
    Raises:
        Exception if all models fail
    """
    if models is None:
        models = [
            "openai/gpt-oss-120b:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "mistralai/devstral-2512:free",
            "xiaomi/mimo-v2-flash:free",
            "google/gemma-3-27b-it:free",
            "google/gemma-3-12b-it:free",
            "deepseek/deepseek-r1-0528:free",
            # "mistralai/mistral-small-3.2-24b-instruct:free",
            # "qwen/qwen3-235b-a22b:free",
            # "microsoft/phi-4-reasoning-plus:free",
        ]
    errors = []
    for model in models:
        try:
            logger.info(f"Trying model: {model} with prompt length: {len(prompt)}")
            completion = client.chat.completions.create(
                extra_body={},
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            if not completion:
                logger.error(f"OpenAI API returned None completion object for model {model}")
                raise Exception(f"OpenAI API returned None completion object for model {model}")
            if not completion.choices:
                logger.error(f"OpenAI API returned empty response for model {model}: {str(completion)}")
                raise Exception(f"Empty response from OpenAI API for model {model}")
            logger.info(f"Model {model} succeeded.")
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenAI API with model {model}: {str(e)}")
            errors.append(f"{model}: {str(e)}")
            continue
    # If all models fail
    logger.error(f"All models failed. Errors: {errors}")
    raise Exception(f"Failed to get response from OpenAI API. Errors: {errors}")

def escape_unescaped_newlines(json_str):
    def replacer(match):
        return match.group(0).replace('\n', '\\n')
    return re.sub(r'\"(.*?)(?<!\\)\"', replacer, json_str, flags=re.DOTALL)

def parse_openai_response(response_content, prefix=None, task_id=None):
    """
    Extract and parse the JSON object that follows the last `prefix` in the model output.
    Handles common noise like markdown fences or trailing commentary.
    """
    orig_content = response_content
    try:
        if prefix:
            matches = list(re.finditer(re.escape(prefix), response_content, flags=re.IGNORECASE))
            if not matches:
                raise ValueError(f"No '{prefix}' found in the response")
            m = matches[-1] 
            response_content = response_content[m.end():].strip()

        candidate = re.sub(r"```(?:json)?|```", "", response_content).strip()

        start = candidate.find("{")
        end   = candidate.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON braces found after prefix")

        json_str = candidate[start:end + 1]

        def _escaper(match):
            return match.group(0).replace("\n", "\\n")
        json_str = re.sub(r'"(?:[^"\\]|\\.)*"', _escaper, json_str, flags=re.DOTALL)

        return json_repair.loads(json_str)

    except Exception as e:
        logger.error(f"JSON parsing error: {e}")
        logger.debug(f"Original model output:\n{orig_content}")
        if task_id:
            set_status(task_id, {"step": "error", "progress": 100, "message": f"Invalid JSON response: {str(e)}"})
        raise


def process_content(content, task_id=None, response_language='en', data_type='business', agent_type=None):
    """
    Process the content using OpenAI API and return the analysis
    Args:
        content: The content to process
        task_id: Optional task ID for status updates
        response_language: Language for the response ('en' or 'ja')
        data_type: The analysis mode ('business' or 'university')
        agent_type: Canonical agent type key when data_type is 'university'
    """
    logger.info("Starting content processing with OpenAI")
    try:
        client = get_openai_client()
        combined_content, domain = build_combined_content(content)

        if data_type == 'university':
            if not agent_type or agent_type not in UNIVERSITY_AGENT_TYPES:
                raise ValueError(f"Unsupported university agent type: {agent_type}")
            agent_meta = UNIVERSITY_AGENT_TYPES[agent_type]

            if task_id:
                set_status(task_id, {
                    "step": "general_knowledge",
                    "progress": 35,
                    "message": "Compiling shared university insights"
                })

            general_prompt = get_university_general_prompt(combined_content, domain)
            specialized_prompt = get_university_specialized_prompt(agent_type, combined_content, domain)

            def general_call():
                logger.debug("Sending university general knowledge OpenAI API request")
                return call_openai(client, general_prompt)

            def specialized_call():
                logger.debug(f"Sending specialized OpenAI API request for {agent_meta['display_name']}")
                if task_id:
                    set_status(task_id, {
                        "step": "specialized_knowledge",
                        "progress": 55,
                        "message": f"Gathering {agent_meta['display_name']} focus"
                    })
                return call_openai(client, specialized_prompt)

            with ThreadPoolExecutor(max_workers=2) as executor:
                future_general = executor.submit(general_call)
                future_specialized = executor.submit(specialized_call)
                general_response = future_general.result()
                specialized_response = future_specialized.result()

            try:
                save_data_with_rotation({"raw_general_response": general_response}, "raw_response_university_general.json", debug=True)
                save_data_with_rotation({"raw_specialized_response": specialized_response}, f"raw_response_{agent_type}.json", debug=True)
            except Exception as e:
                logger.error(f"Failed to save raw university response: {e}")

            general_result = parse_openai_response(general_response, None, task_id)
            specialized_result = parse_openai_response(specialized_response, None, task_id)

            combined_result = {
                "agentType": agent_meta["display_name"],
                "generalKnowledge": general_result,
                "specializedKnowledge": specialized_result,
            }

            if response_language == 'ja':
                logger.info("Translating university data to Japanese")
                combined_result = translate_data_to_japanese(combined_result)

            debug_file = save_data_with_rotation(
                {
                    "prompt_general": general_prompt,
                    "prompt_specialized": specialized_prompt,
                    "parsed_result": combined_result
                },
                f"university_model_response_{agent_type}.json",
                debug=True
            )

            if task_id:
                set_status(task_id, {
                    "step": "agent_profile",
                    "progress": 80,
                    "message": f"Formatting {agent_meta['display_name']} knowledge"
                })
                set_status(task_id, {
                    "step": "done",
                    "progress": 100,
                    "message": "Analysis complete",
                    "result": combined_result
                })
            logger.debug(f"Saved university model response to {debug_file}")
            logger.info("Successfully processed university content with OpenAI")
            return combined_result

        # Default business analysis flow
        if task_id:
            set_status(task_id, {
                "step": "business_overview",
                "progress": 33,
                "message": "Creating business overview"
            })

        main_prompt = get_analysis_prompt().replace("{{WEBSITE_SCRAPED_CONTENT}}", combined_content).replace("${domain}", domain)
        faq_prompt = get_faq_prompt().replace("{{WEBSITE_SCRAPED_CONTENT}}", combined_content)

        def main_call():
            logger.debug("Sending main OpenAI API request")
            if task_id:
                set_status(task_id, {
                    "step": "services_products",
                    "progress": 50,
                    "message": "Analyzing services & products"
                })
            return call_openai(client, main_prompt)

        def faq_call():
            logger.debug("Sending FAQ OpenAI API request")
            return call_openai(client, faq_prompt)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_main = executor.submit(main_call)
            future_faq = executor.submit(faq_call)
            main_response = future_main.result()
            faq_response = future_faq.result()

        try:
            save_data_with_rotation({"raw_response": main_response}, "raw_response_main.json", debug=True)
            save_data_with_rotation({"raw_response": faq_response}, "raw_response_faq.json", debug=True)
        except Exception as e:
            logger.error(f"Failed to save raw response: {e}")

        main_result = parse_openai_response(main_response, None, task_id)
        faq_result = parse_openai_response(faq_response, None, task_id)

        if "faqs" in faq_result:
            main_result["faqs"] = faq_result["faqs"]

        if response_language == 'ja':
            logger.info("Translating data to Japanese")
            main_result = translate_data_to_japanese(main_result)

        debug_file = save_data_with_rotation(
            {
                "prompt": main_prompt,
                "parsed_result": main_result
            },
            "model_response.json",
            debug=True
        )

        if task_id:
            set_status(task_id, {"step": "unique_selling_points", "progress": 66, "message": "Identifying unique selling points"})
            set_status(task_id, {"step": "brand_voice", "progress": 80, "message": "Determining brand voice"})
            set_status(task_id, {"step": "sales_qa", "progress": 90, "message": "Generating sales Q&A"})
            set_status(task_id, {"step": "done", "progress": 100, "message": "Analysis complete", "result": main_result})
        logger.debug(f"Saved model response to {debug_file}")
        logger.info("Successfully processed content with OpenAI")
        return main_result
    except Exception as e:
        logger.error(f"Error processing content with OpenAI: {str(e)}")
        if task_id:
            set_status(task_id, {"step": "error", "progress": 100, "message": str(e)})
        raise

def analyze_url(url, max_pages=1, task_id=None, response_language='en', data_type='business', agent_type=None):
    """
    Scrape URL and analyze its content
    Args:
        url: The URL to analyze
        max_pages: Maximum number of pages to scrape
        task_id: Optional task ID for status updates
        response_language: Language for the response ('en' or 'ja')
        data_type: The analysis mode ('business' or 'university')
        agent_type: Canonical agent type key when data_type is 'university'
    """
    logger.info(f"Starting URL analysis for {url}")
    try:
        content = scrape_url(url, max_pages, task_id=task_id)
        # Only process if we have content
        if not content:
            logger.warning(f"No content found for {url}")
            if task_id:
                set_status(task_id, {"step": "error", "progress": 100, "message": "No content found to analyze"})
            return {"error": "No content found to analyze"}, 400
        # Generate safe filename
        safe_filename = sanitize_filename(url)
        filename = f"{safe_filename}-{max_pages}_pages.json"
        # Save data with rotation policy
        filepath = save_data_with_rotation(content, filename)
        logger.debug(f"Saved scraped data to {filepath}")
        result = process_content(
            content,
            task_id=task_id,
            response_language=response_language,
            data_type=data_type,
            agent_type=agent_type
        )
        logger.info(f"Successfully completed URL analysis for {url}")
        return result, 200
    except Exception as e:
        logger.error(f"Error analyzing URL {url}: {str(e)}")
        if task_id:
            set_status(task_id, {"step": "error", "progress": 100, "message": str(e)})
        raise 
