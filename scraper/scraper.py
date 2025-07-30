from playwright.sync_api import sync_playwright, TimeoutError
from django.forms.models import model_to_dict
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import logging
import random
import time
import json
import re
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reverb.settings")
import django
django.setup()
from .models import Job, Listing
from django.conf import settings


root_url = "https://reverb.com"

logger = logging.getLogger(__name__)

tor_user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:115.0) Gecko/20100101 Firefox/115.0"

desktop_viewport = {
    "width": 1200,
    "height": 800
}

proxy_settings = {
    "server": "socks5://127.0.0.1:9050"
}

def parse_price(price_str):
    price_str = price_str.strip().lower()
    cleaned = re.sub(r'[^\d.]', '', price_str)

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None

def fetch_search_results(search_url):
    listing_urls = []
    count = 1

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            user_agent=tor_user_agent,
            viewport=desktop_viewport,
            proxy=proxy_settings
        )
        page = context.new_page()

        try:

            while True:
                if count == 1:
                    url = search_url
                else:
                    url = search_url + f"&page={count}"

                page.goto(url)
                                 
                class_ = "rc-listing-card__title-link"
                try:
                    page.wait_for_selector("." + class_, timeout=10000)

                except TimeoutError:
                    print("Timeout while waiting for element.")
                    print("Pagination has ended...")
                    break
                soup = BeautifulSoup(page.content(), "html.parser") 
                last_page = not soup.find("div", class_="pagination-container")
                listings = soup.find("ul", class_="rc-listing-grid")
                if not listings:
                    print("No listings found, stopping.")
                    break

                listing_urls.extend([
                    urljoin(
                        root_url,
                        a["href"]
                    )
                    for a in listings.find_all("a", class_=class_) if "?bk=" not in a["href"] 
                ])

                if last_page:
                    break

                count += 1
                time.sleep(random.uniform(1, 3))
        finally:
            context.close()
            browser.close()

    return listing_urls


def scrape_listing_data(listing_url):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            user_agent=tor_user_agent,
            viewport=desktop_viewport,
            proxy=proxy_settings
        )
        page = context.new_page()

        try:

            while True:
                page.goto(listing_url)
                  
                class_ = "spec-list"
                try:
                    page.wait_for_selector("." + class_, timeout=10000)

                except TimeoutError:
                    print("Timeout while waiting for element.")
                    print("Pagination has ended...")
                    break
                soup = BeautifulSoup(page.content(), "html.parser") 
                stats = soup.find("div", class_="item2-stats")
                spec_list = soup.find("table", class_="spec-list")
                price = soup.find(
                    "div", class_="price-with-shipping__price__amount"
                ).find("span", class_="price-display").text
                price = parse_price(price)
                return {
                    "url": listing_url,
                    "title": soup.find("div", class_="item2-title").h1.text,
                    "listed": stats.find("span", class_="weight-bold mr-space").next_sibling,
                    "condition": soup.find("div", class_="condition-display__label").text,
                    "seller": soup.find("div", class_="item2-shop-overview__title").text,
                    "location": soup.find("div", class_="item2-shop-overview__location").text,
                    "price": price,
                }
        finally:
            context.close()
            browser.close()

def process_listing_to_model_instance(listing_dict, job_instance):
    """
    Given a dictionary representing a scraped listing's data and a Job instance,
    return an unsaved Listing model instance populated with that data.
    """
    return Listing(
        job=job_instance,
        title=listing_dict.get("title", "").strip(),
        listed=listing_dict.get("listed", "").strip(),
        condition=listing_dict.get("condition", "").strip(),
        seller=listing_dict.get("seller", "").strip(),
        location=listing_dict.get("location", "").strip(),
        price=listing_dict.get("price", ""),
        url=listing_dict.get("url", "").strip(),
    )

def process_and_save_listings(list_of_listing_dicts, job_instance):
    """
    Process a list of listing dictionaries into Listing model instances,
    then bulk create them in the database.
    """
    instances = [
        process_listing_to_model_instance(d, job_instance)
        for d in list_of_listing_dicts if d
    ]
    Listing.objects.bulk_create(instances)

import json
from decimal import Decimal
from django.forms.models import model_to_dict

def job_to_json(job):
    job_dict = model_to_dict(job, fields=[
        "status",
        "search_url",
        "created_at",
        "started_at",
        "ended_at",
        "error_message",
    ])
    
    for dt_field in ['created_at', 'started_at', 'ended_at']:
        if job_dict.get(dt_field):
            job_dict[dt_field] = job_dict[dt_field].isoformat()

    job_dict['listings'] = []
    for listing in job.listings.all():
        listing_dict = model_to_dict(listing, fields=[
            'url', 'title', 'price', 'seller',
            'location', 'condition', 'listed', 'fetched_at'
        ])

        if listing_dict.get('fetched_at'):
            listing_dict['fetched_at'] = listing_dict['fetched_at'].isoformat()

        if isinstance(listing_dict.get('price'), Decimal):
            listing_dict['price'] = float(listing_dict['price'])
        
        job_dict['listings'].append(listing_dict)

    return json.dumps(job_dict, indent=2)

def run_scraper_for_job(job):
    try:
        job.status = Job.STATUS_RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=['status', 'started_at'])

        listing_urls = fetch_search_results(job.search_url)

        listings_data = []
        for url in listing_urls:
            try:
                data = scrape_listing_data(url)
                if data:
                    data['url'] = url
                    listings_data.append(data)
            except Exception as e:
                logger.warning(f"Failed to scrape listing {url}: {e}")

        process_and_save_listings(listings_data, job)

        job.status = Job.STATUS_COMPLETED
        job.ended_at = timezone.now()
        job.save(update_fields=['status', 'ended_at'])
        
        json_content = job_to_json(job)
        filename = f"job_{job.id}.json"
        json_dir = os.path.join(settings.MEDIA_ROOT, "job_json")
        os.makedirs(json_dir, exist_ok=True)
        file_path = os.path.join(json_dir, filename)

        with open(file_path, "w") as f:
            f.write(json_content)

        job.save()

    except Exception as e:
        logger.error(f"Error in run_scraper_for_job for job #{job.id}: {e}", exc_info=True)
        job.status = Job.STATUS_FAILED
        job.ended_at = timezone.now()
        job.error_message = str(e)
        job.save(update_fields=['status', 'ended_at', 'error_message'])
