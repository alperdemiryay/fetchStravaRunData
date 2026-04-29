import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime
import threading
import time

# ================= CONFIG =================
SOAP_URL = "http://10.207.253.137:9000/marta/webservices/GeneralWebService"
INPUT_FILE = "input.txt"
MAX_THREADS = 10
TPS_LIMIT = 10  # <= 10 requests per second
TIMEOUT = 10
RETRY_COUNT = 2

USERNAME = "admin"
PASSWORD = "UgbVR8GNGYaRrLrU."
# ==========================================

# ---------- RATE LIMITER ----------
class RateLimiter:
    def __init__(self, rate_per_sec):
        self.rate = rate_per_sec
        self.lock = threading.Lock()
        self.tokens = rate_per_sec
        self.last_refill = time.time()

    def acquire(self):
        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_refill

                # refill tokens
                refill = int(elapsed * self.rate)
                if refill > 0:
                    self.tokens = min(self.rate, self.tokens + refill)
                    self.last_refill = now

                if self.tokens > 0:
                    self.tokens -= 1
                    return

            time.sleep(0.01)  # avoid busy wait


rate_limiter = RateLimiter(TPS_LIMIT)

# ---------- LOGGING ----------
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

logging.basicConfig(level=logging.INFO)
success_logger = logging.getLogger("success")
fail_logger = logging.getLogger("fail")

success_handler = logging.FileHandler(f"success_{timestamp}.log")
fail_handler = logging.FileHandler(f"fail_{timestamp}.log")

success_logger.addHandler(success_handler)
fail_logger.addHandler(fail_handler)


# ---------- SOAP ----------
def create_soap_payload(user_param):
    return f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:mar="http://marta.ws.kron.com.tr/marta">
   <soapenv:Header/>
   <soapenv:Body>
      <mar:disconnectUser>
         <!--Optional:-->
         <disconnectUserRequestBean>
            <!--Optional:-->
            <callInfo>
               <!--Optional:-->
               <callerUser>{USERNAME}</callerUser>
               <!--Optional:-->
               <callerUserPassword>{PASSWORD}</callerUserPassword>
               <!--Optional:-->
               <token></token>
               <!--Optional:-->
               <transactionId></transactionId>
            </callInfo>
            <!--Zero or more repetitions:-->
            <keyValue>
               <!--Optional:-->
               <key></key>
               <!--Optional:-->
               <value></value>
            </keyValue>
            <!--Optional:-->
            <userName>{user_param}</userName>
         </disconnectUserRequestBean>
      </mar:disconnectUser>
   </soapenv:Body>
</soapenv:Envelope>"""


def send_request(user_param):
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": ""
    }

    for attempt in range(RETRY_COUNT + 1):
        try:
            # 🔥 THROTTLE HERE
            rate_limiter.acquire()

            response = requests.post(
                SOAP_URL,
                data=create_soap_payload(user_param),
                headers=headers,
                timeout=TIMEOUT
            )

            if response.status_code == 200 and "Fault" not in response.text:
                success_logger.info(user_param)
                return True
            else:
                raise Exception(f"Bad response: {response.status_code}")

        except Exception as e:
            if attempt < RETRY_COUNT:
                continue
            else:
                fail_logger.error(f"{user_param} | ERROR: {str(e)}")
                return False


def main():
    with open(INPUT_FILE, "r") as f:
        users = [line.strip() for line in f if line.strip()]

    print(f"Total records: {len(users)}")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(send_request, user) for user in users]

        for _ in as_completed(futures):
            pass


if __name__ == "__main__":
    main()