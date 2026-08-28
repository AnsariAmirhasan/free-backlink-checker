import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from urllib.parse import urlparse, urljoin
from utils.helper import clean_domain, get_root_domain, sanitize_anchor_text, is_internal_link

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
TIMEOUT = 8

def extract_links_from_page(candidate_url: str, target_domain: str) -> List[Dict[str, Any]]:
    """
    Crawls a candidate referring page, searches for links pointing to target_domain,
    and extracts anchor text, rel attribute, status code, and target landing URL.
    """
    results = []
    target_clean = clean_domain(target_domain)
    target_root = get_root_domain(target_clean)
    
    try:
        resp = requests.get(candidate_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        status_code = resp.status_code
        
        # Only parse successful HTML responses
        content_type = resp.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return results
            
        soup = BeautifulSoup(resp.text, "html.parser")
        page_title = ""
        if soup.title and soup.title.string:
            page_title = soup.title.string.strip()
            
        anchors = soup.find_all("a", href=True)
        for a in anchors:
            raw_href = a["href"].strip()
            if not raw_href or raw_href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
                
            full_href = urljoin(candidate_url, raw_href)
            href_domain = clean_domain(full_href)
            href_root = get_root_domain(href_domain)
            
            # Check if this link points to target domain
            if href_root == target_root:
                # Extract anchor text
                anchor_text = a.get_text(strip=True)
                if not anchor_text:
                    # Check if anchor is an image
                    img = a.find("img")
                    if img and img.get("alt"):
                        anchor_text = f"[IMG: {img.get('alt').strip()}]"
                    elif img:
                        anchor_text = "[IMG: No Alt Text]"
                    else:
                        anchor_text = "[Empty / Icon Anchor]"
                else:
                    anchor_text = sanitize_anchor_text(anchor_text)
                    
                # Extract rel attributes
                rel_list = a.get("rel", [])
                if isinstance(rel_list, str):
                    rel_list = rel_list.lower().split()
                else:
                    rel_list = [r.lower() for r in rel_list]
                    
                link_types = []
                if "nofollow" in rel_list:
                    link_types.append("Nofollow")
                if "ugc" in rel_list:
                    link_types.append("UGC")
                if "sponsored" in rel_list:
                    link_types.append("Sponsored")
                    
                if not link_types:
                    link_type_str = "Dofollow"
                else:
                    link_type_str = ", ".join(link_types)
                    
                results.append({
                    "Referring URL": candidate_url,
                    "Referring Domain": get_root_domain(candidate_url),
                    "Referring Page Title": page_title[:80] if page_title else "N/A",
                    "Target Landing URL": full_href,
                    "Anchor Text": anchor_text,
                    "Link Type": link_type_str,
                    "HTTP Status": status_code,
                    "Is Verified": True
                })
                
    except Exception as e:
        # If fetch failed or timeout, we don't include it in verified links
        pass
        
    return results

def verify_all_candidate_links(candidate_urls: List[str], target_domain: str, max_workers: int = 10, progress_callback=None) -> List[Dict[str, Any]]:
    """
    Multi-threaded verification of candidate referring URLs.
    """
    verified_backlinks: List[Dict[str, Any]] = []
    total = len(candidate_urls)
    completed = 0
    
    if total == 0:
        return verified_backlinks
        
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(extract_links_from_page, url, target_domain): url for url in candidate_urls}
        
        for future in as_completed(futures):
            completed += 1
            if progress_callback:
                progress_callback(completed, total, f"Verifying link on candidate pages: {completed}/{total}")
            try:
                page_links = future.result()
                if page_links:
                    verified_backlinks.extend(page_links)
            except Exception:
                continue
                
    return verified_backlinks
