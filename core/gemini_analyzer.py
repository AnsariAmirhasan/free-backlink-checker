import os
from typing import List, Dict, Any
from google import genai
from google.genai import types

CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-pro"
]

def analyze_backlinks_with_gemini(target_domain: str, backlinks_data: List[Dict[str, Any]], api_key: str = None) -> str:
    """
    Sends backlink profile summary and anchors to Gemini Flash API to generate
    an expert SEO link audit, toxicity report, anchor profile analysis, and link building action plan.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        return "⚠️ **Gemini API Key missing**: Please provide your Gemini API key in the sidebar or `.env` file to unlock AI Link Profile Insights."
    
    if not backlinks_data:
        return "ℹ️ No verified backlinks available to analyze for this domain."
        
    try:
        client = genai.Client(api_key=key)
        
        # Summarize sample data for prompt
        total_links = len(backlinks_data)
        domains = list({item.get("Referring Domain", "N/A") for item in backlinks_data})
        anchors = [item.get("Anchor Text", "N/A") for item in backlinks_data][:40]
        link_types = [item.get("Link Type", "N/A") for item in backlinks_data]
        
        dofollow_count = sum(1 for t in link_types if "dofollow" in str(t).lower())
        nofollow_count = total_links - dofollow_count
        
        prompt = f"""
You are an elite SEO Strategist and Link Profile Auditor. 
Analyze the following backlink data for target domain '{target_domain}':

### DATA OVERVIEW:
- Target Domain: {target_domain}
- Total Discovered Live Backlinks: {total_links}
- Unique Referring Domains ({len(domains)}): {', '.join(domains[:20])}
- Dofollow vs Nofollow: {dofollow_count} Dofollow / {nofollow_count} Nofollow
- Sample Anchor Texts ({len(anchors)}): {', '.join(anchors[:30])}

### INSTRUCTIONS:
Please provide a structured, practical, and punchy SEO Backlink Audit covering:
1. 📊 **Anchor Text Health & Keyword Diversity**: Evaluate the ratio of Branded vs Exact Match vs Generic anchors. Note if there's any over-optimization penalty risk.
2. 🛡️ **Toxic / Spam Link Risk Assessment**: Identify if the referring domains appear natural, educational, directory-based, or potentially spammy.
3. 🔗 **Link Authority & Equity Distribution**: Dofollow/Nofollow balance evaluation.
4. 🚀 **Actionable Link Building Strategy**: 3-4 specific strategies this domain should use to gain more high-authority referring domains in its niche.

Format your response in clean, engaging Markdown with bullet points, emojis, and clear section headers.
"""
        # Try candidate models
        last_error = None
        for model_name in CANDIDATE_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                    )
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                last_error = e
                continue
                
        return f"❌ **Error running Gemini AI Audit**: {str(last_error)}"
        
    except Exception as e:
        return f"❌ **Error running Gemini AI Audit**: {str(e)}"
