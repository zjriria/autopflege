## Bewerbung als Pflegefachmann Automation

This directory contains two ways to automate your applications for the "Ausbildung als Pflegefachmann":

### Option 1: Python Script (`pflegefachmann_bewerbung.py`)
This script uses the Google Maps API to search for institutions (Krankenhaus, Pflegeheim) in a specific city, extracts their emails (if available in their Places details or via a web search), generates a customized cover letter using OpenAI, and sends the email via your Gmail account.

**Prerequisites**:
1. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
2. Your script is completely **API-Key Free**! It uses DuckDuckGo to scrape Google for Hospitals and Emails automatically. You only need your Gmail App Password to send.
   Create a `.env` file in this directory with:
   ```
   GMAIL_USER=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_gmail_app_password
   ```
3. Prepare your application. Put your `Lebenslauf.pdf` and `Zeugnis.pdf` in this folder. The script will automatically merge them using PyPDF2.
4. Run the script:
   ```bash
   python pflegefachmann_bewerbung.py
   ```

### Option 2: n8n Workflow (`n8n_pflegefachmann_workflow.json`)
If you already use n8n (as seen in the YouTube video), we have provided a visual workflow.

**How to Import**:
1. Open your n8n dashboard.
2. Create a "New workflow".
3. In the top right menu (...), click **Import from file**.
4. Select `n8n_pflegefachmann_workflow.json` from this folder.
5. You will need to click on the Nodes to add your credentials (Google Maps API, OpenAI, Gmail).
