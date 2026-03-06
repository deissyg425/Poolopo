import requests
import os
import datetime

# --- SETTINGS ---
START_DATE = datetime.date(2023, 1, 1) 
RESULTS_FILE = "found_magento_sites.txt"
PROGRESS_FILE = "last_date_checked.txt"
HISTORY_FILE = "scanned_history.txt"
BATCH_SIZE = 15000 

def get_last_date():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            content = f.read().strip()
            if content:
                try: return datetime.datetime.strptime(content, "%Y-%m-%d").date()
                except: pass
    return START_DATE

def is_magento_usa(domain):
    try:
        url = f"http://{domain}"
        r = requests.get(url, timeout=4, headers={'User-Agent': 'Mozilla/5.0'}) 
        content = r.text.lower()
        is_magento = "/static/frontend/" in content or "window.checkoutconfig" in content or "mage/cookies" in content
        is_usa = any(x in content for x in ["usa", "united states", "shipping to us", "usd"]) or domain.endswith(".us")
        return is_magento and is_usa
    except:
        return False

def run_hunt():
    target_date = get_last_date()
    if target_date >= datetime.date.today():
        print("All caught up!")
        return

    scanned = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                scanned.add(line.strip())

    print(f"--- Starting 15k Batch for: {target_date} ---")
    # FIXED URL BELOW
    feed_url = f"https://raw.githubusercontent.com{target_date}.txt"
    
    try:
        response = requests.get(feed_url)
        if response.status_code != 200:
            print(f"No data found for {target_date}. Moving to next day...")
        else:
            domains = response.text.splitlines()
            found_count = 0
            with open(RESULTS_FILE, "a") as rf, open(HISTORY_FILE, "a") as hf:
                processed = 0
                for domain in domains:
                    if processed >= BATCH_SIZE: break
                    if domain in scanned: continue
                    
                    print(f"Checking: {domain}...", end=" ")
                    if is_magento_usa(domain):
                        print("!!! FOUND US MAGENTO SITE !!!")
                        rf.write(f"{domain} (Added: {target_date})\n")
                        found_count += 1
                    else:
                        print("Not Magento.")
                    
                    hf.write(domain + "\n")
                    processed += 1
            print(f"Finished. Found {found_count} US Magento stores.")
        
        with open(PROGRESS_FILE, "w") as f:
            f.write(str(target_date + datetime.timedelta(days=1)))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_hunt()
