import os
import time
import random
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_2CAPTCHA = "http://2captcha.com/in.php"
RESULT_2CAPTCHA = "http://2captcha.com/res.php"
SITE_KEY = "6LeUcBMlAAAAAJ6epJwL4MTmUVeMTFVdc7-1_RGV"
FAUCET_URL = "https://faucet.octra.network/"
CLAIM_ENDPOINT = "https://faucet.octra.network/api/faucet"
BALANCE_ENDPOINT = "https://faucet.octra.network/api/balance"
APIKEY = os.getenv("APIKEY_2CAPTCHA")
LOG_FILE = "success_log.txt"

with open("wallets.txt") as f:
    WALLETS = [line.strip() for line in f if line.strip()]

with open("proxies.txt") as f:
    PROXIES = [line.strip() for line in f if line.strip()]


def log_success(wallet, tx_hash, balance):
    with open(LOG_FILE, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {wallet} | TX: {tx_hash} | Balance: {balance}\n")


def get_proxy_session(proxy_url):
    session = requests.Session()
    session.proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    return session


def solve_captcha(session, wallet, attempt=1):
    print(f"[{wallet}] 🔐 CAPTCHA Attempt #{attempt}")
    payload = {
        'key': APIKEY,
        'method': 'userrecaptcha',
        'googlekey': SITE_KEY,
        'pageurl': FAUCET_URL,
        'json': 1
    }
    try:
        r = session.post(API_2CAPTCHA, data=payload, timeout=30).json()
        if r.get("status") != 1:
            print(f"[{wallet}] ❌ Submit captcha gagal: {r}")
            return None

        captcha_id = r["request"]
        print(f"[{wallet}] CAPTCHA ID: {captcha_id}")
        for _ in range(30):
            time.sleep(5)
            res = session.get(RESULT_2CAPTCHA, params={
                'key': APIKEY,
                'action': 'get',
                'id': captcha_id,
                'json': 1
            }).json()
            if res.get("status") == 1:
                print(f"[{wallet}] ✅ CAPTCHA sukses.")
                return res["request"]
            elif res.get("request") != "CAPCHA_NOT_READY":
                print(f"[{wallet}] ❌ CAPTCHA gagal: {res}")
                return None
            print(f"[{wallet}] ⏳ Menunggu CAPTCHA...")
    except Exception as e:
        print(f"[{wallet}] 🔴 ERROR CAPTCHA: {e}")
    return None


def get_balance(session, wallet):
    try:
        r = session.get(f"{BALANCE_ENDPOINT}?address={wallet}", timeout=15)
        res = r.json()
        balance = res.get("balance", "N/A")
        print(f"[{wallet}] 💰 Balance: {balance}")
        return balance
    except Exception as e:
        print(f"[{wallet}] ⚠️ Gagal cek saldo: {e}")
        return "Unknown"


def claim(wallet, proxy):
    session = get_proxy_session(proxy)
    max_captcha_attempts = 3
    max_claim_retries = 3

    for captcha_attempt in range(1, max_captcha_attempts + 1):
        token = solve_captcha(session, wallet, captcha_attempt)
        if not token:
            print(f"[{wallet}] ❗ Gagal CAPTCHA (percobaan {captcha_attempt}/{max_captcha_attempts})")
            if captcha_attempt == max_captcha_attempts:
                print(f"[{wallet}] ⛔ Melewati wallet karena CAPTCHA gagal")
            time.sleep(10)
            continue

        for retry in range(max_claim_retries):
            try:
                payload = {
                    "address": wallet,
                    "g-recaptcha-response": token
                }
                headers = {"Content-Type": "application/json"}

                print(f"[{wallet}] 🚀 Klaim faucet... (percobaan {retry+1}/{max_claim_retries})")
                r = session.post(CLAIM_ENDPOINT, json=payload, headers=headers, timeout=30)

                if r.status_code != 200:
                    print(f"[{wallet}] ⚠️ HTTP Error: {r.status_code}")
                    time.sleep(5)
                    continue

                res = r.json()

                if res.get("message") == "Success":
                    tx_hash = res.get("txHash", "Unknown")
                    print(f"[{wallet}] ✅ Klaim BERHASIL!")
                    print(f"[{wallet}] 🔗 TX Hash: {tx_hash}")
                    balance = get_balance(session, wallet)
                    log_success(wallet, tx_hash, balance)
                    return

                else:
                    print(f"[{wallet}] ❌ Klaim gagal: {res}")
                    break

            except Exception as e:
                print(f"[{wallet}] 🔴 ERROR klaim: {e}")
                time.sleep(5)

        print(f"[{wallet}] ⛔ Klaim gagal setelah beberapa percobaan.")
        break


def main():
    for i, wallet in enumerate(WALLETS):
        proxy = PROXIES[i % len(PROXIES)]
        print(f"\n===[ Wallet #{i+1} | {wallet} | Proxy: {proxy} ]===")
        claim(wallet, proxy)
        delay = random.randint(20, 40)
        print(f"[Delay] ⏱️ Menunggu {delay} detik...\n")
        time.sleep(delay)


if __name__ == "__main__":
    main()
