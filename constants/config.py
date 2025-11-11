# captcha challenger
CHALLENGE_KEYWORDS = [
    "captcha", "recaptcha", "cloudflare", "cf-chl", "please enable javascript",
    "are you human", "verify you are a human", "access to this site is restricted",
    "our systems have detected unusual traffic"
]

# max tries per topic
MAX_RETRIES = 2

# retry backoff in seconds
RETRY_BACKOFF = (1, 3)  # seconds

# threshold to consider content sufficient
MIN_CONTENT_WORDS = 20

# keywords to look for in content filtering
KEYWORDS = ["services", "CEO", "founder", "clients", "products", "solutions", "funding"]