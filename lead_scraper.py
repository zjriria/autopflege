import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time

# Regex pattern to identify valid email addresses
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# Keywords to prioritize HR emails over generic info emails
HR_KEYWORDS = ['bewerbung', 'personal', 'karriere', 'hr']

def scrape_emails_from_website(base_url):
    print(f"🔍 Scanning: {base_url}")
    found_emails = set()
    
    # Common subpages where German clinics hide their application emails
    pages_to_check = [
        base_url,
        f"{base_url}/karriere",
        f"{base_url}/stellenangebote",
        f"{base_url}/impressum",
        f"{base_url}/kontakt"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for page in pages_to_check:
        try:
            response = requests.get(page, headers=headers, timeout=10)
            # Only proceed if the page actually exists
            if response.status_code == 200:
                # Extract text from the HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                
                # Find all email matches using Regex
                emails_on_page = re.findall(EMAIL_REGEX, text)
                
                for email in emails_on_page:
                    email_clean = email.lower()
                    # Filter out common junk emails or image file names that look like emails
                    if not email_clean.endswith(('.png', '.jpg', '.jpeg', '.gif', '.sentry')):
                        found_emails.add(email_clean)
            
            # Be polite to their servers
            time.sleep(1) 
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Could not access {page}: {e}")
            continue

    return list(found_emails)

def select_best_email(email_list):
    """Prioritizes 'Bewerbung' or 'Personal' emails over generic 'info' emails."""
    if not email_list:
        return None
        
    for email in email_list:
        if any(keyword in email for keyword in HR_KEYWORDS):
            return email # Return the first HR-specific email found
            
    return email_list[0] # Fallback to the first email found if no HR email exists

# ==========================================
# 🚀 Execution & Excel Export
# ==========================================
if __name__ == "__main__":
    print("🤖 Reading target clinics from Excel...")
    try:
        df_in = pd.read_excel("found_clinics_sachsen.xlsx")
        target_clinics = df_in.to_dict('records')
    except Exception as e:
        print(f"Error loading Excel: {e}")
        target_clinics = []

    results = []

    for clinic in target_clinics:
        if len(results) >= 10:
            print("🛑 Reached exactly 10 successful leads! Stopping scraper.")
            break
            
        all_emails = scrape_emails_from_website(clinic["URL"])
        best_email = select_best_email(all_emails)
        
        if best_email:
            print(f"✅ Found target email for {clinic['Clinic Name']}: {best_email}")
            results.append({
                "Clinic Name": clinic["Clinic Name"],
                "Email": best_email,
                "Contact Person": "Sehr geehrte Damen und Herren", # Default fallback for your bot
                "City": "Sachsen"
            })
        else:
            print(f"❌ No emails found for {clinic['Clinic Name']}")

    # Export directly to the Excel format your main bot reads
    if results:
        df = pd.DataFrame(results)
        df.to_excel("scraped_leads.xlsx", index=False)
        print("\n🎉 Scraping complete! Saved to scraped_leads.xlsx")
        print("You can now rename this file to 'input.xlsx' to feed it directly into your application bot!")
