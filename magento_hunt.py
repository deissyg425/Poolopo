import requests
import os
import datetime

# --- SETTINGS ---
START_DATE = datetime.date(2021, 1, 1) 
TECH_FILE = "found_magento_tech.txt"
FASH_FILE = "found_magento_fashion.txt"
DATE_FILE = "last_date_checked.txt"
BATCH_SIZE = 60000 

def get_last_date():
    if os.path.exists(DATE_FILE):
        with open(DATE_FILE, "r") as f:
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
        is_magento = "/static/frontend/" in content or "window.checkoutconfig" in content
        is_usa = any(x in content for x in ["usa", "united states", "shipping to us"]) or domain.endswith(".us")
        if is_magento and is_usa:
            if any(k in content for k in ["iphone", "samsung", "phone", "electronics"]): return "tech"
            if any(k in content for k in ["clothing", "jewelry", "fashion"]): return "fashion"
        return None
    except: return None

def run_hunt():
    t_date = get_last_date()
    if t_date >= datetime.date.today(): return
    print(f"--- 60k Batch for: {t_date} ---")
    
    # THE FIXED LINK - I MANUALLY TYPED THE SLASH
    feed_url = "https://raw.githubusercontent.com" + str(t_date) + ".txt"
    
    try:
        resp = requests.get(feed_url)
        if resp.status_code == 200:
            domains = resp.text.splitlines()
            processed = 0
            with open(TECH_FILE, "a") as mt, open(FASH_FILE, "a") as mf:
                for d in domains:
                    if processed >= BATCH_SIZE: break
                    clean = d.strip().lower()
                    if not clean: continue
                    if processed % 500 == 0: print(f"Checked {processed} domains...")
                    res = check_site(clean)
                    if res == "tech": mt.write(f"{clean}\n")
                    elif res == "fashion": mf.write(f"{clean}\n")
                    processed += 1
            print(f"Finished {processed} domains.")
        else: print(f"No data for {t_date}.")
        with open(DATE_FILE, "w") as f: f.write(str(t_date + datetime.timedelta(days=1)))
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    run_hunt()
