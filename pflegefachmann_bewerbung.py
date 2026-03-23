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
import fitz  # PyMuPDF for compression
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import google.generativeai as genai

# Load environment variables (e.g., GMAIL_USER, GMAIL_APP_PASSWORD)
# This no longer needs Google Maps or OpenAI API keys!
load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER", "your_email@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "your_app_password")

MY_NAME = "Zakariae Jriria"
MY_PHONE = "(+212) 660 944 365"
CITY_TO_SEARCH = "Berlin"
NUM_RESULTS = 10

# --- 0. CONFIGURATION & TOGGLES ---
ENABLE_TIME_GATING = False  # Set to True to only send Tue-Thu 08:30-11:00 CET
HAS_B2_CERTIFICATE = True   # Set to True to inject B2 sentence in the email
ENABLE_AI_CONTENT = True    # Set to True to dynamically generate the opening paragraph via Gemini

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
    
    # Compress using PyMuPDF (Upgrade 3)
    compressed_name = output_filename
    try:
        doc = fitz.open(output_filename)
        doc.save("compressed_" + output_filename, garbage=4, deflate=True, clean=True)
        doc.close()
        # Replace original with compressed if successful
        os.replace("compressed_" + output_filename, output_filename)
        print(f"Successfully created and compressed {output_filename} to bypass IT Firewalls.")
    except Exception as e:
        print(f"Successfully created {output_filename} (Compression skipped: {e})")
        
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
    cp_lower = contact_person.lower().strip()
    
    if "frau" in cp_lower:
        name = contact_person.replace("Frau", "").replace("frau", "").strip()
        greeting = f"Sehr geehrte Frau {name}," if name else "Sehr geehrte Damen und Herren,"
    elif "herr" in cp_lower:
        name = contact_person.replace("Herrn", "").replace("herrn", "").replace("Herr", "").replace("herr", "").strip()
        greeting = f"Sehr geehrter Herr {name}," if name else "Sehr geehrte Damen und Herren,"
    elif contact_person != "Sehr geehrte Damen und Herren":
        greeting = f"Sehr geehrte(r) {contact_person},"
    else:
        greeting = "Sehr geehrte Damen und Herren,"
        
    # Upgrade 5: Language Certificate Dynamic Injector
    cert_mention = " Mein B2-Zertifikat für die deutsche Sprache sowie meinen umfassenden Lebenslauf finden Sie im Anhang." if HAS_B2_CERTIFICATE else " Im Anhang finden Sie meine vollständigen Bewerbungsunterlagen."
    
    # Upgrade 1: AI-Powered Dynamic Content
    dynamic_opening = f"ich werde nicht behaupten, dass ich bereits perfekt bin. Aber ich bin überzeugt, dass meine bisherigen Erfahrungen und meine Leidenschaft für die Pflege mich zu einem geeigneten Kandidaten für das Team der Einrichtung {clinic_name} machen."
    
    if ENABLE_AI_CONTENT and GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Erstelle genau EINEN hochprofessionellen, begeisterten Einleitungssatz auf Deutsch für ein kurzes Anschreiben für eine Ausbildung als 'Pflegefachmann' bei der Einrichtung '{clinic_name}'. Der Satz soll erklären, warum der Bewerber sich aufgrund des hervorragenden Rufs ausgerechnet dort bewirbt. Keine Anrede, keine Grußformel. Nur der reine Satz ohne Anführungszeichen. Erster Buchstabe klein geschrieben, da er nach der Anrede (Sehr geehrte...,) kommt."
            response = model.generate_content(prompt)
            if response.text:
                dynamic_opening = response.text.replace('"', '').strip()
                # Ensure starts with lowercase to follow 'Sehr geehrte X,'
                dynamic_opening = dynamic_opening[0].lower() + dynamic_opening[1:]
                print(f"[AI] Generated custom opening for {clinic_name}: {dynamic_opening}")
        except Exception as e:
            print(f"[AI Error] Konnte keinen Satz generieren, verwende Standard-Einleitung: {e}")
            
    return f"""{greeting}

{dynamic_opening}

Durch mein sechsmonatiges Praktikum im medizinischen Bereich konnte ich bereits erste praktische Einblicke in die Welt der Pflege und Medizin gewinnen. Ich habe gelernt, Vitalzeichen zu kontrollieren, bei Untersuchungen zu assistieren, mit Patienten einfühlsam umzugehen und auch in herausfordernden Situationen ruhig zu bleiben. Besonders in der Zusammenarbeit mit dem Rettungsteam und im direkten Patientenkontakt habe ich gespürt: Das ist mein Weg.

Die enge Zusammenarbeit mit dem Rettungsteam hat mir außerdem gezeigt, wie wichtig Verlässlichkeit und Teamgeist in diesem Beruf sind. Genau diese Eigenschaften möchte ich bei Ihnen einbringen – verbunden mit der Motivation, mich ständig weiterzuentwickeln.

Über die Möglichkeit, mich Ihnen in einem Vorstellungsgespräch näher vorzustellen, würde ich mich sehr freuen.{cert_mention}

Mit freundlichen Grüßen,
{MY_NAME}
{MY_PHONE}
"""

def send_email(to_email, subject, body, attachment_path):
    """Send an email via Gmail SMTP with the merged PDF attachment."""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg['Bcc'] = "zakariaejriria@gmail.com" # BCC yourself
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
    
    if os.path.exists("converted_output.csv"):
        clinics_file = "converted_output.csv"
    elif os.path.exists("input.xlsx"):
        clinics_file = "input.xlsx"
    else:
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
    
    print(f"Versand aus Datei: '{clinics_file}'...")
    
    if clinics_file.endswith(".xlsx"):
        df = pd.read_excel(clinics_file)
        for _, row in df.iterrows():
            email = str(row.get("Email", "")).strip()
            if email and email.lower() != "nan":
                # Handle possible varying column names gracefully
                clinic_name = row.get("Clinic Name", row.get("Name", "Unbekannt"))
                clinics_to_email.append({
                    "Clinic Name": str(clinic_name) if not pd.isna(clinic_name) else "Unbekannt",
                    "Contact Person": str(row.get("Contact Person", "Sehr geehrte Damen und Herren")) if "Contact Person" in df.columns else "Sehr geehrte Damen und Herren",
                    "Email": email,
                    "City": str(row.get("City", CITY_TO_SEARCH)) if "City" in df.columns else CITY_TO_SEARCH
                })
    else:
        with open(clinics_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email_raw = str(row.get("email", row.get("Email", ""))).strip()
                if email_raw:
                    email_first = email_raw.split(",")[0].strip()
                    if email_first and email_first.lower() != "nan":
                        clinics_to_email.append({
                            "Clinic Name": str(row.get("firma", row.get("Clinic Name", "Unbekannt"))),
                            "Contact Person": str(row.get("person", row.get("Contact Person", "Sehr geehrte Damen und Herren"))),
                            "Email": email_first,
                            "City": str(row.get("adresse", row.get("City", CITY_TO_SEARCH)))
                        })
                
    if not clinics_to_email:
        print("Keine Emails in der Datei gefunden!")
        return
            
    print(f"Versand an {len(clinics_to_email)} Kontakte wird gestartet...\n")
    
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
        success = send_email(email, subject, body, merged_pdf)
        # success = True 
        print(f"REAL SEND ACTIVATED! Live email sent to: {email}")
        # ---------
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        status_text = "Sent" if success else "Failed"
        
        # Upgrade 2: Smart Time-Gating
        if ENABLE_TIME_GATING:
            while True:
                now = datetime.now()
                # 1=Tue, 2=Wed, 3=Thu. Between 08:30 and 11:00
                if now.weekday() in [1, 2, 3] and 8 <= now.hour < 11:
                    if now.hour == 8 and now.minute < 30:
                        pass # too early
                    else:
                        break # In optimal sending window!
                print(f"[{now.strftime('%H:%M')}] Outside optimal HR hours (Tue-Thu 08:30-11:00). Snoozing for 10 minutes...")
                time.sleep(600)
        
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
            delay = 30
            print(f"Log 'Sent' in '{sent_file}' gespeichert. Warte {delay} Sekunden...")
            time.sleep(delay)
        else:
            print(f"Log 'Failed' in '{sent_file}' gespeichert. Fahre fort...")

    print("\nAlle Bewerbungen verarbeitet! Überprüfe 'applications_sent.csv' für die Historie.")

if __name__ == "__main__":
    main()
