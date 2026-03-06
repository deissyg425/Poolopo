import requests
import os
import datetime

# --- SETTINGS ---
START_DATE = datetime.date(2023, 1, 1) 
MAGENTO_TECH_FILE = "found_magento_tech.txt"
MAGENTO_FASHION_FILE = "found_magento_fashion.txt"
EXCLUSIVE_TECH_FILE = "found_exclusive_electronics.txt"
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

def check_site(domain):
    try:
        url = f"http://{domain}"
        r = requests.get(url, timeout=4, headers={'User-Agent': 'Mozilla/5.0'}) 
        content = r.text.lower()
        tech_kw = ["iphone", "samsung", "smartphone", "mobile phone", "gadget", "electronics", "laptop"]
        is_refurbished = any(x in content for x in ["refurbished", "renewed", "pre-owned"])
        is_fashion = any(kw in content for kw in ["clothing", "jewelry", "fashion", "necklace"])
        is_magento = any(x in content for x in ["/static/frontend/", "window.checkoutconfig", "mage/cookies"])
        is_shopify = "cdn.shopify.com" in content
        is_woo = "woocommerce" in content
        is_bigcom = "bigcommerce" in content
        is_usa = any(x in content for x in ["usa", "united states", "shipping to us"]) or domain.endswith(".us")
        if is_magento and is_usa:
            if any(kw in content for kw in tech_kw): return "magento_tech"
            if is_fashion: return "magento_fashion"
        if any(kw in content for kw in tech_kw):
            if is_shopify or is_woo: return None
            if is_bigcom:
                return "exclusive_tech" if is_refurbished else None
            return "exclusive_tech"
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
    
    print(f"--- Starting 15k Batch for: {target_date} ---")
    
    # THE FIXED LINK
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
                    clean_domain = domain.strip().lower()
                    if not clean_domain or clean_domain in memory: continue
                    print(f"Checking: {clean_domain}...", end=" ")
                    result = check_site(clean_domain)
                    if result == "magento_tech":
                        print("!!! MAGENTO TECH !!!")
                        mt.write(f"{clean_domain} (Added: {target_date})\n")
                    elif result == "magento_fashion":
                        print("!!! MAGENTO FASHION !!!")
                        mf.write(f"{clean_domain} (Added: {target_date})\n")
                    elif result == "exclusive_tech":
                        print("!!! EXCLUSIVE TECH !!!")
                        ef.write(f"{clean_domain} (Added: {target_date})\n")
                    else: print("No.")
                    hf.write(clean_domain + "\n")
                    processed += 1
            with open(PROGRESS_FILE, "w") as f:
                f.write(str(target_date + datetime.timedelta(days=1)))
        else:
            print(f"No data for {target_date}. Skipping.")
            with open(PROGRESS_FILE, "w") as f:
                f.write(str(target_date + datetime.timedelta(days=1)))
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    run_hunt()
