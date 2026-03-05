import requests
import os
import datetime

# --- CONFIGURATION ---
START_DATE = datetime.date(2025, 1, 1)
HISTORY_FILE = "scanned_history.txt"  # This is the "Memory"
RESULTS_FILE = "found_magento_sites.txt"
PROGRESS_FILE = "last_date_checked.txt"

def get_last_date():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return datetime.datetime.strptime(f.read().strip(), "%Y-%m-%d").date()
    return START_DATE

def is_magento_usa(domain):
    try:
        url = f"http://{domain}"
        # We check the site for Magento code and USA mentions
        r = requests.get(url, timeout=10)
        content = r.text.lower()
        is_magento = "/static/frontend/" in content or "window.checkoutconfig" in content
        is_usa = any(x in content for x in ["usa", "united states", "shipping to us"]) or domain.endswith(".us")
        return is_magento and is_usa
    except:
        return False

def run_hunt():
    target_date = get_last_date()
    today = datetime.date.today()

    if target_date >= today:
        print("All caught up! Checking today's new domains...")
        target_date = today

    # Load history to ensure NO REPEATS
    scanned = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            scanned = {line.strip() for line in f}

    print(f"--- Hunting: {target_date} ---")
    
    # Fetch daily list from a public domain archive
    feed_url = f"https://raw.githubusercontent.com{target_date}.txt"
    
    try:
        response = requests.get(feed_url)
        if response.status_code != 200:
            print(f"No data for {target_date}, moving to next day.")
        else:
            domains = response.text.splitlines()
            found_count = 0
            
            # Process a batch of 400 domains to keep GitHub happy
            with open(RESULTS_FILE, "a") as rf, open(HISTORY_FILE, "a") as hf:
                for domain in domains[:400]:
                    if domain in scanned: continue
                    
                    print(f"Checking: {domain}")
                    if is_magento_usa(domain):
                        print("FOUND!")
                        rf.write(f"{domain} (Registered: {target_date})\n")
                        found_count += 1
                    
                    hf.write(domain + "\n") # Save to memory
                    scanned.add(domain)

            print(f"Finished {target_date}. Found {found_count} sites.")
        
        # Save progress to move forward tomorrow
        with open(PROGRESS_FILE, "w") as f:
            f.write(str(target_date + datetime.timedelta(days=1)))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_hunt()
