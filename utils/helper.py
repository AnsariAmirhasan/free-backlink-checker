import re
from urllib.parse import urlparse

def clean_domain(raw_url: str) -> str:
    """
    Extracts the clean host domain from a given raw URL or domain string.
    Example: 'https://www.cairindia.com/products' -> 'cairindia.com'
    """
    if not raw_url:
        return ""
    
    url = str(raw_url).strip().lower()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.split(":")[0]  # Remove port if present
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return raw_url.strip().lower()

def get_root_domain(url_or_domain: str) -> str:
    """
    Extracts the registered root domain (e.g. 'sub.cairindia.com' -> 'cairindia.com')
    using pure python with tldextract fallback.
    """
    if not url_or_domain:
        return ""
    cleaned = clean_domain(url_or_domain)
    parts = cleaned.split(".")
    if len(parts) >= 3:
        # Check common 2-part ccTLDs like .co.in, .com.au, .co.uk, .org.in, .gov.in
        if parts[-2] in ["co", "com", "org", "net", "gov", "edu", "ac"] and len(parts[-1]) == 2:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])
    return cleaned

def is_internal_link(target_domain: str, candidate_url: str) -> bool:
    """
    Checks whether a candidate URL belongs to the same root domain as the target.
    """
    target_root = get_root_domain(target_domain)
    candidate_root = get_root_domain(candidate_url)
    return bool(target_root and candidate_root and target_root == candidate_root)

def sanitize_anchor_text(text: str) -> str:
    """
    Cleans up whitespace and formatting in anchor text.
    """
    if not text:
        return "[Brand / Domain Anchor]"
    cleaned = re.sub(r'\s+', ' ', str(text)).strip()
    return cleaned if cleaned else "[Brand / Domain Anchor]"
