import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY_2CAPTCHA")
SITE_KEY = "6LcRmiYoAAAAAEfbmR0ocXJqGpEvq5rw9Cw1kFVt"
PAGE_URL = "https://faucet.octra.network"
FAUCET_URL = "https://faucet.octra.network/api/claim"
LOG_FILE = "faucet_log.txt"

def log(message):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {message}\n")
    print(f"{timestamp} {message}")

def get_captcha_token():
    # Kirim task captcha
    resp = requests.post("http://2captcha.com/in.php", data={
        "key": API_KEY,
        "method": "userrecaptcha",
        "googlekey": SITE_KEY,
        "pageurl": PAGE_URL,
        "json": 1
    }).json()
    
    if resp["status"] != 1:
        raise Exception(f"Gagal submit captcha: {resp}")
    
    captcha_id = resp["request"]
    log(f"Captcha task ID: {captcha_id}")

    # Ambil hasil captcha
    for i in range(20):
        time.sleep(5)
        result = requests.get("http://2captcha.com/res.php", params={
            "key": API_KEY,
            "action": "get",
            "id": captcha_id,
            "json": 1
        }).json()
        if result["status"] == 1:
            return result["request"]
        log(f"Menunggu captcha... ({i+1}/20)")
    raise Exception("Timeout captcha.")

def claim_faucet(address):
    for attempt in range(1, 4):
        try:
            log(f"[{address}] Attempt #{attempt} - Get Captcha")
            captcha_token = get_captcha_token()

            payload = {
                "address": address,
                "isValidator": False,
                "captchaToken": captcha_token
            }

            headers = {"Content-Type": "application/json"}
            response = requests.post(FAUCET_URL, json=payload, headers=headers)
            result = response.json()

            if result.get("success"):
                log(f"[{address}] ✅ SUCCESS: {result}")
                return True
            else:
                log(f"[{address}] ❌ ERROR: {result.get('message')}")
        except Exception as e:
            log(f"[{address}] ❌ EXCEPTION: {str(e)}")
        time.sleep(5)
    return False

def load_wallets(filename="wallets.txt"):
    if not os.path.exists(filename):
        log("File wallets.txt tidak ditemukan.")
        return []
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip().startswith("octra")]

def main():
    wallets = load_wallets()
    if not wallets:
        log("Tidak ada wallet untuk diproses.")
        return
    log(f"Mulai claim untuk {len(wallets)} wallet...")
    for addr in wallets:
        claim_faucet(addr)
    log("SELESAI semua wallet.")

if __name__ == "__main__":
    main()
