import os
import time
import random
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from duckduckgo_search import DDGS
import requests
import re
from PyPDF2 import PdfMerger
from dotenv import load_dotenv

# Load environment variables (e.g., GMAIL_USER, GMAIL_APP_PASSWORD)
# This no longer needs Google Maps or OpenAI API keys!
load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER", "your_email@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "your_app_password")

MY_NAME = "Zakariae Jriria"
MY_PHONE = "(+212) 660 944 365"
CITY_TO_SEARCH = "Berlin"
NUM_RESULTS = 10

# --- 1. PDF MERGING ---
def merge_documents(output_filename="Bewerbung_Pflegefachmann.pdf"):
    """Merges all necessary application documents into a single PDF."""
    print("Checking for PDF documents to merge...")
    
    # Place these files in the same folder as the script
    docs_to_merge = ["Lebenslauf.pdf", "Anschreiben.pdf", "Zertifikat_B2.pdf", "Zeugnis.pdf"]
    existing_docs = [doc for doc in docs_to_merge if os.path.exists(doc)]
    
    if not existing_docs:
        print("No PDF documents found to merge! Please place 'Lebenslauf.pdf', etc. in the script folder.")
        return None
        
    print(f"Merging the following documents: {existing_docs}")
    merger = PdfMerger()
    
    for pdf in existing_docs:
        merger.append(pdf)
    
    merger.write(output_filename)
    merger.close()
    print(f"Successfully created {output_filename}")
    return output_filename

# --- 2. NO-API CLINIC SCRAPER ---
def extract_emails_from_url(url):
    """Visits a website and uses regex to find email addresses."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64 AppleWebKit/537.36)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, response.text)
        
        # Filter junk emails
        valid_emails = [e for e in emails if not e.endswith(('.png', '.jpg', '.gif', 'wixpress.com'))]
        return list(set(valid_emails))
    except Exception as e:
        print(f"  [!] Could not read {url}")
        return []

def find_clinics(city, num_results=5):
    """Searches for clinics via DuckDuckGo and scrapes their emails (API-Key Free)."""
    search_query = f"Krankenhaus Pflegeheim {city} Kontakt Impressum"
    results_list = []
    
    print(f"Searching DuckDuckGo for clinics in {city}...")
    with DDGS() as ddgs:
        try:
            results = list(ddgs.text(search_query, max_results=num_results, backend="html"))
        except Exception as e:
            print(f"DuckDuckGo Rate Limit Hit: {e}. Try again later or use an API.")
            results = []
        for result in results:
            title = result.get('title', 'Unknown Clinic')
            url = result.get('href', '')
            
            print(f"Checking: {title} ({url})")
            emails = extract_emails_from_url(url)
            
            contact_email = emails[0] if emails else None
            
            if contact_email:
                results_list.append({
                    "Clinic Name": title.split('-')[0].strip(), # Clean up the title a bit
                    "Contact Person": "Sehr geehrte Damen und Herren",
                    "Email": contact_email,
                    "City": city
                })
            time.sleep(3) # Polite scraping delay to avoid DDOSing DuckDuckGo
            
    return results_list

# --- 3. EMAIL TEMPLATE & SENDING ---
def create_email_body(clinic_name, contact_person="Sehr geehrte Damen und Herren"):
    """Generates the highly professional German email body."""
    if contact_person != "Sehr geehrte Damen und Herren":
        greeting = f"Sehr geehrte(r) Frau/Herr {contact_person},"
    else:
        greeting = f"{contact_person},"
        
    return f"""{greeting}

ich werde nicht behaupten, dass ich bereits perfekt bin. Aber ich bin überzeugt, dass meine bisherigen Erfahrungen und meine Leidenschaft für die Pflege mich zu einem geeigneten Kandidaten für das Team der Einrichtung {clinic_name} machen.

Durch mein sechsmonatiges Praktikum im medizinischen Bereich konnte ich bereits erste praktische Einblicke in die Welt der Pflege und Medizin gewinnen. Ich habe gelernt, Vitalzeichen zu kontrollieren, bei Untersuchungen zu assistieren, mit Patienten einfühlsam umzugehen und auch in herausfordernden Situationen ruhig zu bleiben. Besonders in der Zusammenarbeit mit dem Rettungsteam und im direkten Patientenkontakt habe ich gespürt: Das ist mein Weg.

Die enge Zusammenarbeit mit dem Rettungsteam hat mir außerdem gezeigt, wie wichtig Verlässlichkeit und Teamgeist in diesem Beruf sind. Genau diese Eigenschaften möchte ich bei Ihnen einbringen – verbunden mit der Motivation, mich ständig weiterzuentwickeln.

Über die Möglichkeit, mich Ihnen in einem Vorstellungsgespräch näher vorzustellen, würde ich mich sehr freuen. Im Anhang finden Sie meine vollständigen Bewerbungsunterlagen.

Mit freundlichen Grüßen,
{MY_NAME}
{MY_PHONE}
"""

def send_email(to_email, subject, body, attachment_path):
    """Send an email via Gmail SMTP with the merged PDF attachment."""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Attach the merged PDF
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)
    else:
        print("Warning: Attachment not found! Sending without CV.")

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False

# --- 4. DATA LOGGING & AUTOMATION ---
def main():
    print("=== Pflegefachmann Bewerbungs-Roboter ===")
    
    clinics_file = "clinics.csv"
    
    # ---------------------------------------------------------
    # PHASE 1 & 2: Scrape & Build clinics.csv if it doesn't exist
    # (The Scraper Reality Check)
    # ---------------------------------------------------------
    if not os.path.exists(clinics_file):
        print(f"[!] '{clinics_file}' nicht gefunden. Starte Web-Scraper, um Kliniken in {CITY_TO_SEARCH} zu suchen...")
        clinics = find_clinics(CITY_TO_SEARCH, num_results=NUM_RESULTS)
        
        with open(clinics_file, mode="w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Clinic Name", "Contact Person", "Email", "City"])
            writer.writeheader()
            writer.writerows(clinics)
            
        print(f"\n[✓] {len(clinics)} Kliniken gefunden und in '{clinics_file}' gespeichert.")
        print("\n=== PHASE 1 ABGESCHLOSSEN ===")
        print("WICHTIG (Dein Launch-Plan Phase 1 & 2):")
        print("1. THE SELF-TEST: Ändere die erste Zeile in 'clinics.csv' zu deiner eigenen E-Mail und teste den Versand!")
        print("2. DATA CLEANUP: Überprüfe die echten E-Mail-Adressen manuell (lösche 'datenschutz@...', 'webmaster@...' etc.).")
        print("3. Starte dieses Skript danach erneut, um Phase 3 (Merge) und 4 (Soft Launch) zu starten!")
        return

    # ---------------------------------------------------------
    # PHASE 3 & 4: Merge files and Send applications from clinics.csv
    # ---------------------------------------------------------
    print(f"[+] '{clinics_file}' gefunden. Lese Daten und bereite den Versand vor...")
    
    # 1. Merge Documents (Phase 3: File Preparation)
    merged_pdf_name = f"Bewerbung_Pflegefachmann_{MY_NAME.replace(' ', '_')}.pdf"
    merged_pdf = merge_documents(merged_pdf_name)
    if not merged_pdf:
        print("Warnung: Keine PDF gefunden. Setze ohne Anhang fort...")
        
    # 2. Track already sent (CSV)
    sent_file = "applications_sent.csv"
    sent_emails = set()
    
    if os.path.exists(sent_file):
        with open(sent_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sent_emails.add(row["Email"])
    else:
        # Create new logging file
        with open(sent_file, mode="w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Clinic Name", "Contact Person", "Email", "City", "Status", "Date Sent"])
            writer.writeheader()
            
    # Read manually reviewed clinics
    clinics_to_email = []
    with open(clinics_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clinics_to_email.append(row)
            
    print(f"Versand an {len(clinics_to_email)} Kontakte aus '{clinics_file}' wird gestartet...\n")
    
    # Send Loop
    for clinic in clinics_to_email:
        email = clinic["Email"]
        clinic_name = clinic["Clinic Name"]
        
        if email in sent_emails:
            print(f"Bereits an {email} ({clinic_name}) beworben. Überspringe...")
            continue
            
        print(f"\n[+] Bereite Bewerbung vor für {clinic_name} ({email})")
        body = create_email_body(clinic_name, clinic.get("Contact Person", "Sehr geehrte Damen und Herren"))
        subject = f"Bewerbung um einen Ausbildungsplatz als Pflegefachmann – {MY_NAME}"
        
        # ---------
        # IMPORTANT (Phase 4: Soft Launch): Uncomment the next line to ACTUALLY send emails for real!
        # success = send_email(email, subject, body, merged_pdf)
        success = True 
        print(f"MOCKED SEND: Email text ready. Remove the comment in the code to send.")
        # ---------
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        status_text = "Sent" if success else "Failed"
        
        # Log the status immediately to CSV
        with open(sent_file, mode="a", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Clinic Name", "Contact Person", "Email", "City", "Status", "Date Sent"])
            writer.writerow({
                "Clinic Name": clinic_name,
                "Contact Person": clinic.get("Contact Person", "Unbekannt"),
                "Email": email,
                "City": clinic.get("City", CITY_TO_SEARCH),
                "Status": status_text,
                "Date Sent": timestamp
            })
        
        if success:
            # Anti-Spam Logic
            delay = random.uniform(45, 120)
            print(f"Log 'Sent' in '{sent_file}' gespeichert. Warte {delay:.0f} Sekunden zum Spam-Schutz...")
            time.sleep(delay)
        else:
            print(f"Log 'Failed' in '{sent_file}' gespeichert. Fahre fort...")

    print("\nAlle Bewerbungen verarbeitet! Überprüfe 'applications_sent.csv' für die Historie.")

if __name__ == "__main__":
    main()
