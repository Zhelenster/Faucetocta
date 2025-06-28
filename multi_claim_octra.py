import os
import time
import random
import requests
from dotenv import load_dotenv

load_dotenv()

API_2CAPTCHA = "http://2captcha.com/in.php"
RESULT_2CAPTCHA = "http://2captcha.com/res.php"
SITE_KEY = "6LeUcBMlAAAAAJ6epJwL4MTmUVeMTFVdc7-1_RGV"
FAUCET_URL = "https://faucet.octra.network/"
CLAIM_ENDPOINT = "https://faucet.octra.network/api/faucet"
APIKEY = os.getenv("APIKEY_2CAPTCHA")

# === Load Wallets and Proxies ===
with open("wallets.txt") as f:
    WALLETS = [line.strip() for line in f if line.strip()]

with open("proxies.txt") as f:
    PROXIES = [line.strip() for line in f if line.strip()]


def get_proxy_session(proxy_url):
    session = requests.Session()
    session.proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    return session


def solve_captcha(session, wallet):
    print(f"[{wallet}] Mengirim CAPTCHA...")
    payload = {
        'key': APIKEY,
        'method': 'userrecaptcha',
        'googlekey': SITE_KEY,
        'pageurl': FAUCET_URL,
        'json': 1
    }
    try:
        r = session.post(API_2CAPTCHA, data=payload, timeout=30).json()
        if r["status"] != 1:
            print(f"[{wallet}] Gagal submit captcha: {r}")
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
            if res["status"] == 1:
                print(f"[{wallet}] CAPTCHA sukses.")
                return res["request"]
            elif res["request"] != "CAPCHA_NOT_READY":
                print(f"[{wallet}] CAPTCHA gagal: {res}")
                return None
            print(f"[{wallet}] Menunggu CAPTCHA...")

    except Exception as e:
        print(f"[{wallet}] ERROR CAPTCHA: {e}")
    return None


def claim(wallet, proxy):
    session = get_proxy_session(proxy)
    token = solve_captcha(session, wallet)
    if not token:
        print(f"[{wallet}] ❌ Gagal selesaikan CAPTCHA.")
        return

    try:
        payload = {
            "address": wallet,
            "g-recaptcha-response": token
        }
        headers = {
            "Content-Type": "application/json"
        }

        print(f"[{wallet}] Klaim faucet...")
        r = session.post(CLAIM_ENDPOINT, json=payload, headers=headers, timeout=30)
        res = r.json()
        if res.get("message") == "Success":
            print(f"[{wallet}] ✅ Klaim BERHASIL!")
        else:
            print(f"[{wallet}] ❌ Gagal: {res}")
    except Exception as e:
        print(f"[{wallet}] ❌ ERROR Klaim: {e}")


def main():
    for i, wallet in enumerate(WALLETS):
        proxy = PROXIES[i % len(PROXIES)]
        print(f"\n===[ Wallet #{i+1} | {wallet} | Proxy: {proxy} ]===")
        claim(wallet, proxy)
        delay = random.randint(20, 40)
        print(f"[Delay] Menunggu {delay} detik...\n")
        time.sleep(delay)


if __name__ == "__main__":
    main()
