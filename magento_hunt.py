import requests
import os
import datetime

# --- SETTINGS ---
START_DATE = datetime.date(2021, 1, 1) 
MAGENTO_TECH_FILE = "found_magento_tech.txt"
MAGENTO_FASHION_FILE = "found_magento_fashion.txt"
EXCLUSIVE_TECH_FILE = "found_exclusive_electronics.txt"
PROGRESS_FILE = "last_date_checked.txt"
HISTORY_FILE = "scanned_history.txt"
BATCH_SIZE = 60000  # THE 60K GOAL

def get_last_date():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            content = f.read().strip()
            if content:
                try: return datetime.datetime.strptime(content, "%Y-%m-%d").date()
                except: pass
    return START_DATE

def check_site(domain):
    """Turbo Filter: High speed, short timeout."""
    try:
        url = f"http://{domain}"
        # Shorter timeout (2.5s) to maintain 60k speed
        r = requests.get(url, timeout=2.5, headers={'User-Agent': 'Mozilla/5.0'}) 
        content = r.text.lower()
        
        tech_kw = ["iphone", "samsung", "smartphone", "mobile phone", "gadget", "electronics", "laptop"]
        fashion_kw = ["clothing", "jewelry", "fashion", "necklace", "apparel", "watch"]
        
        is_magento = any(x in content for x in ["/static/frontend/", "window.checkoutconfig", "mage/cookies"])
        is_usa = any(x in content for x in ["usa", "united states", "shipping to us", "usd"]) or domain.endswith(".us")
        
        if is_magento and is_usa:
            if any(kw in content for kw in tech_kw): return "magento_tech"
            if any(kw in content for kw in fashion_kw): return "magento_fashion"
            
        if any(kw in content for kw in tech_kw):
            is_shopify = "cdn.shopify.com" in content
            is_woo = "woocommerce" in content
            if not (is_shopify or is_woo): return "exclusive_tech"
            
        return None
    except: return None

def run_hunt():
    target_date = get_last_date()
    if target_date >= datetime.date.today():
        print("All caught up!")
        return

    memory = set()
    for f_name in [MAGENTO_TECH_FILE, MAGENTO_FASHION_FILE, EXCLUSIVE_TECH_FILE, HISTORY_FILE]:
        if os.path.exists(f_name):
            with open(f_name, "r") as f:
                for line in f:
                    d = line.split(" ").strip().lower()
                    if d: memory.add(d)

    print(f"--- 60k Speed Run for: {target_date} ---")
    base = "https://raw.githubusercontent.com"
    feed_url = f"{base}{target_date}.txt"
    
    try:
        response = requests.get(feed_url)
        if response.status_code == 200:
            domains = response.text.splitlines()
            processed = 0
            with open(MAGENTO_TECH_FILE, "a") as mt, open(MAGENTO_FASHION_FILE, "a") as mf, \
                 open(EXCLUSIVE_TECH_FILE, "a") as ef, open(HISTORY_FILE, "a") as hf:
                for domain in domains:
                    if processed >= BATCH_SIZE: break
                    clean = domain.strip().lower()
                    if not clean or clean in memory: continue
                    
                    res = check_site(clean)
                    if res:
                        print(f"FOUND: {clean} ({res})")
                        if res == "magento_tech": mt.write(f"{clean} (Date: {target_date})\n")
                        elif res == "magento_fashion": mf.write(f"{clean} (Date: {target_date})\n")
                        elif res == "exclusive_tech": ef.write(f"{clean} (Date: {target_date})\n")
                    
                    hf.write(clean + "\n")
                    processed += 1
            print(f"Finished {processed} sites for {target_date}.")
        else:
            print(f"No data for {target_date}. Skipping.")

        # Always move to the next day
        with open(PROGRESS_FILE, "w") as f:
            f.write(str(target_date + datetime.timedelta(days=1)))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_hunt()
