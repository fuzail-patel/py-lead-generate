from constants.config import MIN_CONTENT_WORDS, KEYWORDS
from constants.userAgents import USER_AGENTS
import random
from urllib.parse import parse_qs, unquote, urlparse
import re

def is_sufficient_content(text: str) -> bool:
    if not text or not isinstance(text, str):
        return False
    clean_text = text.strip().lower()
    if len(clean_text) < MIN_CONTENT_WORDS:
        return False
    if "no useful content" in clean_text or "not found" in clean_text:
        return False
    return True


def is_search_blocked(html) -> bool:
    if not html or not isinstance(html, str):
        return False
    html_lower = html.lower()
    block_indicators = [
        "unfortunately, bots use duckduckgo too",
        "please complete the following challenge",
        "select all squares containing a duck",
        "anomaly-modal__puzzle",
        "error-lite@duckduckgo.com",
        "cloudflare",
        "captcha",
    ]
    return any(i in html_lower for i in block_indicators)


def choose_ua():
    return random.choice(USER_AGENTS)


def choose_lang():
    return random.choice(
        [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.8",
            "en-CA,en;q=0.8",
            "en-AU,en;q=0.8",
            "en-IN,en;q=0.8",
        ]
    )


def extract_real_url(duck_link: str) -> str:
    parsed = urlparse(duck_link)
    qs = parse_qs(parsed.query)
    if "uddg" in qs:
        return unquote(qs["uddg"][0])
    return duck_link


def search_headers(block_resources=True):
    """
    Generate headers for web requests optimized for HTML text scraping.
    
    Args:
        block_resources: If True, only accepts HTML/text (blocks images, CSS, media)
                        This reduces bandwidth and speeds up requests without affecting scraper.
                        The scraper only extracts text from HTML, so images/CSS/media are not needed.
    """
    ua = choose_ua()
    lang = choose_lang()
    
    # Optimized Accept header - only HTML/text, explicitly reject images/CSS/media
    # This tells servers we only want HTML content, reducing response size
    if block_resources:
        # Prioritize HTML, XML; reject images, CSS, JavaScript, fonts, media
        accept_header = "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8"
    else:
        accept_header = random.choice(
            [
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "text/html,application/xml;q=0.9,image/webp,*/*;q=0.8",
            ]
        )
    
    headers = {
        "User-Agent": ua,
        "Accept-Language": lang,
        "Accept": accept_header,
        "Cache-Control": random.choice(["max-age=0", "no-cache", "no-store"]),
        "Accept-Encoding": random.choice(["gzip, deflate, br", "gzip, deflate"]),
        "Upgrade-Insecure-Requests": random.choice(["1", None]),
        "Sec-Fetch-Site": random.choice(["same-origin", "none", "cross-site"]),
        "Sec-Fetch-Mode": random.choice(["navigate", "no-cors"]),
        "Sec-Fetch-User": random.choice(["?1", None]),
        "Sec-Fetch-Dest": random.choice(["document", "empty"]),
        "Connection": random.choice(["keep-alive", "close"]),
    }

    if random.random() < 0.7:
        headers["Referer"] = random.choice(
            [
                "https://duckduckgo.com/",
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://search.brave.com/",
            ]
        )
    if random.random() < 0.5:
        headers["DNT"] = random.choice(["1", "0"])
    if random.random() < 0.4:
        headers["Pragma"] = "no-cache"
    if random.random() < 0.3:
        headers["TE"] = "trailers"

    headers = {k: v for k, v in headers.items() if v is not None}
    return headers

import re

def is_navigational_content(text: str, min_words: int = 5) -> bool:
    # Check for minimal word count
    if len(text.split()) < min_words:
        return False
    # Skip purely navigational or generic content
    if re.search(r"(click here|privacy|terms|login|subscribe|©|all rights reserved)", text, re.I):
        return True
    return False

def contains_keywords(text: str, keywords=KEYWORDS):
    """
    Check if text contains any keywords.
    Optimized: assumes text is already lowercased for better performance.
    """
    # If text is already lowercased (from caller), use it directly
    if isinstance(text, str):
        text_lower = text.lower() if not text.islower() else text
    else:
        text_lower = str(text).lower()
    
    # Use any() with generator for early exit
    return any(k.lower() in text_lower for k in keywords)