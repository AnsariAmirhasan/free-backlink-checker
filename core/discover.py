import re
import requests
import json
from typing import Set, List, Dict, Any
from urllib.parse import urlparse, quote_plus
from utils.helper import clean_domain, is_internal_link, get_root_domain

DEFAULT_TIMEOUT = 8
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-pro"
]

def get_headers():
    return {
        "User-Agent": USER_AGENTS[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

def discover_gemini_grounded(domain: str, gemini_api_key: str = None) -> List[Dict[str, str]]:
    """
    Uses Google Gemini to find known referring domains, mentions, industry sources,
    Wikipedia citations, and directories linking to the domain.
    """
    results = []
    if not gemini_api_key:
        return results
        
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=gemini_api_key)
        
        prompt = f"""
Identify actual external web pages, trade directories, industry blogs, vendor listings, news articles, or partner sites that link to or reference '{domain}'.

Return ONLY a JSON array of objects with keys: "url", "domain", "anchor_or_context".
Example:
[
  {{"url": "https://www.indiamart.com/company/...", "domain": "indiamart.com", "anchor_or_context": "{domain}"}},
  {{"url": "https://en.wikipedia.org/wiki/...", "domain": "wikipedia.org", "anchor_or_context": "Official Website"}}
]

Do not return internal links from {domain}. Return at least 15-30 realistic external URLs.
"""
        response_text = None
        for m in CANDIDATE_MODELS:
            try:
                resp = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                if resp and resp.text:
                    response_text = resp.text
                    break
            except Exception:
                continue
                
        if response_text:
            cleaned_text = response_text.strip()
            data = json.loads(cleaned_text)
            if isinstance(data, list):
                for item in data:
                    u = item.get("url")
                    if u and u.startswith(("http://", "https://")) and not is_internal_link(domain, u):
                        results.append({
                            "url": u,
                            "anchor": item.get("anchor_or_context", domain),
                            "domain": get_root_domain(u)
                        })
    except Exception as e:
        print(f"Gemini grounded discovery error: {e}")
        
    return results

def discover_alienvault(domain: str) -> Set[str]:
    discovered = set()
    try:
        url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/url_list?limit=50&page=1"
        resp = requests.get(url, headers=get_headers(), timeout=DEFAULT_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("url_list", []):
                page_url = item.get("url")
                if page_url and page_url.startswith(("http://", "https://")):
                    if not is_internal_link(domain, page_url):
                        discovered.add(page_url)
    except Exception:
        pass
    return discovered

def discover_wayback_cdx(domain: str) -> Set[str]:
    discovered = set()
    try:
        url = f"https://web.archive.org/cdx/search/cdx?url=*{domain}*&output=json&limit=60"
        resp = requests.get(url, headers=get_headers(), timeout=DEFAULT_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 1:
                for row in data[1:]:
                    if len(row) > 2:
                        orig = row[2]
                        if orig.startswith(("http://", "https://")) and not is_internal_link(domain, orig):
                            discovered.add(orig)
    except Exception:
        pass
    return discovered

def discover_duckduckgo_lite(domain: str) -> Set[str]:
    discovered = set()
    queries = [
        f'"{domain}" -site:{domain}',
        f'"{domain}"'
    ]
    for q in queries:
        try:
            url = "https://lite.duckduckgo.com/lite/"
            resp = requests.post(url, data={"q": q}, headers=get_headers(), timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                urls = re.findall(r'class=[\"\']result-link[\"\']\s+href=[\"\'](https?://[^\"\']+)[\"\']', resp.text)
                if not urls:
                    urls = re.findall(r'href=[\"\'](https?://[^\"\'\s>]+)[\"\']', resp.text)
                for u in urls:
                    if not is_internal_link(domain, u) and "duckduckgo.com" not in u:
                        discovered.add(u)
        except Exception:
            continue
    return discovered

def discover_all_candidate_referrers(domain: str, gemini_api_key: str = None, progress_callback=None) -> Dict[str, Any]:
    clean_dom = clean_domain(domain)
    all_urls: Set[str] = set()
    gemini_links: List[Dict[str, str]] = []
    
    if progress_callback:
        progress_callback("🔎 Scanning Web Archives & Passive Repositories (Wayback CDX & AlienVault)...")
    
    wb_links = discover_wayback_cdx(clean_dom)
    all_urls.update(wb_links)
    
    av_links = discover_alienvault(clean_dom)
    all_urls.update(av_links)
    
    if progress_callback:
        progress_callback(f"🌐 Querying Open Search & Footprints... ({len(all_urls)} candidates found)")
    
    ddg_links = discover_duckduckgo_lite(clean_dom)
    all_urls.update(ddg_links)
    
    if gemini_api_key:
        if progress_callback:
            progress_callback("🧠 Querying Gemini AI web intelligence for referring domains & citations...")
        gemini_links = discover_gemini_grounded(clean_dom, gemini_api_key)
        for item in gemini_links:
            all_urls.add(item["url"])
            
    filtered_list = [u for u in all_urls if u and not is_internal_link(clean_dom, u)]
    
    return {
        "candidate_urls": sorted(filtered_list),
        "gemini_links": gemini_links
    }
