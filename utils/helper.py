import re
from urllib.parse import urlparse
import tldextract

def clean_domain(raw_url: str) -> str:
    """
    Extracts the clean host domain from a given raw URL or domain string.
    Example: 'https://www.example.com/blog/page' -> 'example.com'
    """
    if not raw_url:
        return ""
    
    url = raw_url.strip().lower()
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
    Extracts the registered root domain (e.g. 'blog.example.co.uk' -> 'example.co.uk')
    """
    try:
        extracted = tldextract.extract(url_or_domain)
        if extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"
        return extracted.domain or url_or_domain
    except Exception:
        return clean_domain(url_or_domain)

def is_internal_link(target_domain: str, candidate_url: str) -> bool:
    """
    Checks whether a candidate URL belongs to the same root domain as the target.
    """
    target_root = get_root_domain(target_domain)
    candidate_root = get_root_domain(candidate_url)
    return target_root == candidate_root

def sanitize_anchor_text(text: str) -> str:
    """
    Cleans up whitespace and formatting in anchor text.
    """
    if not text:
        return "[No Anchor / Image Link]"
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned if cleaned else "[Empty Anchor]"
