# Reverb Scraper (Django Project)

A Django web app that scrapes Reverb.com listings from a search URL you provide and exports the data in JSON format.

## What it does

- Submit any Reverb.com search URL via the dashboard.
- Uses Celery with Redis to run distributed, asynchronous scraping tasks.
- Employs Playwright in headless mode to render pages and bypass bot detection.
- Routes requests through the Tor network for IP rotation and basic evasion.
- Parses HTML content with BeautifulSoup for reliable data extraction.
- Scrapes listing details: title, price, seller, location, condition, and time since posted.
- Export scraped data as JSON.

The deployment at the demo site runs with limited server resources—please use search queries that return a reasonable number of results for the smoothest test experience.
---
*For demonstration and review purposes only.*
