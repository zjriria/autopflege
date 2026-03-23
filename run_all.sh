#!/bin/bash

echo "======================================"
echo "🚀 STARTING NURSING AUTOMATION PIPELINE"
echo "======================================"

echo "--> [1/3] Searching for Hospitals via OpenStreetMap..."
python clinic_finder.py

echo "--> [2/3] Scraping HR Emails from Hospital Websites..."
python lead_scraper.py

# Move newly generated leads to input.xlsx for the main bot
if [ -f "scraped_leads.xlsx" ]; then
    mv scraped_leads.xlsx input.xlsx
    echo "--> Successfully queued scraped leads!"
else
    echo "--> No new leads found by the scraper. Using existing data..."
fi

echo "--> [3/3] Generating AI Cover Letters & Sending Emails..."
python pflegefachmann_bewerbung.py

echo "======================================"
echo "✅ PIPELINE RUN COMPLETE               "
echo "======================================"
