import requests
import os
import datetime

# --- SETTINGS ---
START_DATE = datetime.date(2021, 1, 1) 
MAGENTO_TECH_FILE = "found_magento_tech.txt"
MAGENTO_FASHION_FILE = "found_magento_fashion.txt"
PROGRESS_FILE = "last_date_checked.txt"
BATCH_SIZE = 60000 

def get_last_date():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            content = f.read().strip()
            if content:
                try: return datetime.datetime.strptime(content, "%Y-%m-%d").date()
                except: pass
    return START_DATE

def check_site(domain):
    try:
        url = f"http://{domain}"
        r = requests.get(url, timeout=2, headers={'User-Agent': 'Mozilla/5.0'}) 
        content = r.text.lower()
        tech_kw = ["iphone", "samsung", "smartphone", "mobile phone", "gadget", "electronics"]
        fashion_kw = ["clothing", "jewelry", "fashion", "necklace"]
        is_magento = "/static/frontend/" in content or "window.checkoutconfig" in content
        is_usa = any(x in content for x in ["usa", "united states", "shipping to us"]) or domain.endswith(".us")
        if is_magento and is_usa:
            if any(kw in content for kw in tech_kw): return "magento_tech"
            if any(kw in content for kw in fashion_kw): return "magento_fashion"
        return None
    except: return None

def run_hunt():
    target_date = get_last_date()
    if target_date >= datetime.date.today():
        print("All caught up!")
        return
    print(f"--- 60k Batch for: {target_date} ---")
    
    # THE FIXED LINK - ONE SOLID PIECE
    feed_url = f"https://raw.githubusercontent.com{target_date}.txt"
    
    try:
        response = requests.get(feed_url)
        if response.status_code == 200:
            domains = response.text.splitlines()
            processed = 0
            with open(MAGENTO_TECH_FILE, "a") as mt, open(MAGENTO_FASHION_FILE, "a") as mf:
                for domain in domains:
                    if processed >= BATCH_SIZE: break
                    clean = domain.strip().lower()
                    if not clean: continue
                    if processed % 500 == 0: print(f"Checked {processed} sites...")
                    res = check_site(clean)
                    if res == "magento_tech": mt.write(f"{clean}\n")
                    elif res == "magento_fashion": mf.write(f"{clean}\n")
                    processed += 1
            print(f"Finished {processed} sites.")
        else: print(f"No data for {target_date}. Skipping.")
        with open(PROGRESS_FILE, "w") as f: f.write(str(target_date + datetime.timedelta(days=1)))
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    run_hunt()
