# News Scraper and Database Loader

This Python project scrapes news data from BBC, CNN, and Dawn websites, processes it, and stores the extracted information in a PostgreSQL database.

## Features

- Scrapes headlines, descriptions, URLs, and content from:
  - **BBC News**
  - **CNN**
  - **Dawn News**
- Cleans and preprocesses text data by removing special characters.
- Stores the extracted data into a PostgreSQL database with a structured schema.
- Handles errors gracefully during web scraping and database operations.

---

## Prerequisites

1. **Python 3.8+**
2. Install required Python libraries:
   ```bash
   pip install requests beautifulsoup4 html5lib psycopg2-binary
   ```
