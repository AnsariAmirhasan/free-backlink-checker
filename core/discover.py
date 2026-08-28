import re
import requests
from typing import Set, List
from duckduckgo_search import DDGS
from utils.helper import clean_domain, is_internal_link

DEFAULT_TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def discover_hackertarget(domain: str) -> Set[str]:
    """
    Queries HackerTarget free backlink endpoint.
    """
    discovered = set()
    try:
        url = f"https://api.hackertarget.com/backlinks/?q={domain}"
        resp = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if resp.status_code == 200:
            lines = resp.text.splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith("http://") or line.startswith("https://"):
                    if not is_internal_link(domain, line):
                        discovered.add(line)
    except Exception as e:
        print(f"HackerTarget discovery error: {e}")
    return discovered

def discover_search_engines(domain: str, max_results: int = 40) -> Set[str]:
    """
    Searches DuckDuckGo for web pages mentioning or linking to the domain outside itself.
    """
    discovered = set()
    queries = [
        f'"{domain}" -site:{domain}',
        f'intext:"{domain}" -site:{domain}',
        f'"{domain}"'
    ]
    
    try:
        ddgs = DDGS()
        for q in queries:
            try:
                results = list(ddgs.text(q, max_results=max_results))
                for item in results:
                    href = item.get("href")
                    if href and href.startswith(("http://", "https://")):
                        if not is_internal_link(domain, href):
                            discovered.add(href)
            except Exception as e:
                print(f"DDG query failed for '{q}': {e}")
                continue
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        
    return discovered

def discover_alienvault(domain: str) -> Set[str]:
    """
    Queries AlienVault OTX URL intelligence endpoint.
    """
    discovered = set()
    try:
        url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/url_list?limit=50&page=1"
        resp = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            url_list = data.get("url_list", [])
            for item in url_list:
                page_url = item.get("url")
                if page_url and page_url.startswith(("http://", "https://")):
                    if not is_internal_link(domain, page_url):
                        discovered.add(page_url)
    except Exception as e:
        print(f"AlienVault OTX error: {e}")
    return discovered

def discover_urlscan(domain: str) -> Set[str]:
    """
    Queries URLScan.io public index for pages that reference or link to the domain.
    """
    discovered = set()
    try:
        url = f"https://urlscan.io/api/v1/search/?q=domain:{domain}&size=30"
        resp = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            for item in results:
                page_url = item.get("page", {}).get("url")
                if page_url and page_url.startswith(("http://", "https://")):
                    if not is_internal_link(domain, page_url):
                        discovered.add(page_url)
    except Exception as e:
        print(f"URLScan error: {e}")
    return discovered

def discover_all_candidate_referrers(domain: str, progress_callback=None) -> List[str]:
    """
    Runs all free discovery engines and aggregates unique external referring page candidates.
    """
    clean_dom = clean_domain(domain)
    all_candidates: Set[str] = set()
    
    if progress_callback:
        progress_callback("🔍 Querying HackerTarget Backlink API...")
    ht_links = discover_hackertarget(clean_dom)
    all_candidates.update(ht_links)
    
    if progress_callback:
        progress_callback(f"🔎 Querying Search Footprints (DuckDuckGo)... ({len(all_candidates)} found so far)")
    ddg_links = discover_search_engines(clean_dom, max_results=30)
    all_candidates.update(ddg_links)
    
    if progress_callback:
        progress_callback(f"🌐 Querying AlienVault OTX Web Intelligence... ({len(all_candidates)} found so far)")
    av_links = discover_alienvault(clean_dom)
    all_candidates.update(av_links)

    if progress_callback:
        progress_callback(f"📡 Querying URLScan Public Records... ({len(all_candidates)} found so far)")
    us_links = discover_urlscan(clean_dom)
    all_candidates.update(us_links)
    
    # Filter out empty or duplicate entries
    final_list = [url for url in all_candidates if url and not is_internal_link(clean_dom, url)]
    return sorted(final_list)
