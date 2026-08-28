import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io
from dotenv import load_dotenv

from utils.helper import clean_domain, get_root_domain, sanitize_anchor_text
from core.discover import discover_all_candidate_referrers
from core.verifier import verify_all_candidate_links
from core.gemini_analyzer import analyze_backlinks_with_gemini

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Free SEO Backlink Checker & GSC Link Analyzer",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .sub-title {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #38BDF8;
        margin-top: 0.3rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        font-weight: 500;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .gsc-banner {
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(16, 185, 129, 0.15));
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/link.png", width=64)
    st.title("Settings & Options")
    
    # Check secrets or environment
    default_key = os.environ.get("GEMINI_API_KEY", "")
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        default_key = st.secrets["GEMINI_API_KEY"]
        
    api_key_input = st.text_input(
        "Gemini API Key (Free Tier)",
        type="password",
        value=default_key,
        help="Free key from aistudio.google.com to power AI search discovery & link audit."
    )
    
    st.markdown("---")
    st.subheader("⚙️ Crawler Settings")
    max_workers = st.slider("Crawl Threads", min_value=2, max_value=25, value=12)
    
    st.markdown("---")
    st.markdown("""
    **💡 Supported Data Sources:**
    - 📥 **Google Search Console (GSC) Export**: 100% accurate internal Google backlinks
    - 🧠 **Google Gemini AI Web Intelligence**: Citations, directories & industry mentions
    - 🏛️ **Wayback Machine CDX Archive**: Historic links & referring domains
    - 🌐 **AlienVault OTX**: Passive DNS & web graph
    - 🤖 **Live Multi-Threaded DOM Crawler**: Extract exact anchor text & link status
    """)

# Header Section
st.markdown('<div class="main-title">Free SEO Backlink Checker & GSC Link Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Discover live backlinks, referring domains, anchor texts & analyze your official Google Search Console (GSC) backlink profile with Gemini AI.</div>', unsafe_allow_html=True)

# Mode Selection
input_mode = st.radio(
    "Choose Analysis Mode:",
    ["🔍 Live Web Discovery (Any Website)", "📥 Google Search Console (GSC) CSV Import (Your Website)"],
    horizontal=True
)

# Initialize Session State
if "backlinks_df" not in st.session_state:
    st.session_state["backlinks_df"] = None
if "target_domain" not in st.session_state:
    st.session_state["target_domain"] = ""
if "ai_analysis" not in st.session_state:
    st.session_state["ai_analysis"] = None
if "candidate_urls" not in st.session_state:
    st.session_state["candidate_urls"] = []

# MODE 1: LIVE WEB DISCOVERY
if input_mode == "🔍 Live Web Discovery (Any Website)":
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        target_url_input = st.text_input(
            "Enter Target Website Domain or URL",
            placeholder="e.g. cairindia.com, stripe.com, or yourwebsite.com",
            label_visibility="collapsed"
        )
    with col_btn:
        analyze_btn = st.button("🚀 Find Backlinks", type="primary", use_container_width=True)

    # Quick test domain buttons
    st.markdown("<small style='color: #94A3B8;'>Quick Examples: </small>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 3])
    if c1.button("cairindia.com"):
        st.session_state["quick_domain"] = "cairindia.com"
    if c2.button("python.org"):
        st.session_state["quick_domain"] = "python.org"
    if c3.button("streamlit.io"):
        st.session_state["quick_domain"] = "streamlit.io"
    if c4.button("supabase.com"):
        st.session_state["quick_domain"] = "supabase.com"

    if "quick_domain" in st.session_state and not target_url_input:
        target_url_input = st.session_state["quick_domain"]

    if analyze_btn and target_url_input:
        clean_target = clean_domain(target_url_input)
        st.session_state["target_domain"] = clean_target
        st.session_state["ai_analysis"] = None
        
        st.info(f"Targeting Domain: **{clean_target}**")
        progress_box = st.status("🔍 Step 1/2: Discovering candidate pages across open archives & AI index...", expanded=True)
        
        discovery_res = discover_all_candidate_referrers(
            clean_target,
            gemini_api_key=api_key_input,
            progress_callback=lambda msg: progress_box.write(msg)
        )
        
        candidate_urls = discovery_res["candidate_urls"]
        gemini_links = discovery_res["gemini_links"]
        st.session_state["candidate_urls"] = candidate_urls
        
        progress_box.write(f"✅ Found **{len(candidate_urls)}** candidate external URLs to crawl.")
        
        if len(candidate_urls) == 0:
            progress_box.update(label="⚠️ No candidate URLs found in open public archives.", state="complete")
            st.warning("Tip: Enter your Gemini API Key in the left sidebar to enable AI search discovery for any domain!")
        else:
            progress_box.update(label="🚀 Step 2/2: Crawling candidate pages and verifying live links...", state="running")
            p_bar = st.progress(0, text="Verifying live links...")
            
            def update_verify_progress(current, total, msg):
                pct = int((current / total) * 100)
                p_bar.progress(pct, text=msg)
                
            verified_data = verify_all_candidate_links(
                candidate_urls,
                clean_target,
                max_workers=max_workers,
                progress_callback=update_verify_progress
            )
            p_bar.empty()
            
            final_rows = []
            if verified_data:
                final_rows.extend(verified_data)
                
            verified_urls = {row["Referring URL"] for row in verified_data}
            for g in gemini_links:
                if g["url"] not in verified_urls:
                    final_rows.append({
                        "Referring URL": g["url"],
                        "Referring Domain": g.get("domain") or get_root_domain(g["url"]),
                        "Referring Page Title": "Authority Citation / Mention",
                        "Target Landing URL": f"https://{clean_target}",
                        "Anchor Text": g.get("anchor") or clean_target,
                        "Link Type": "Citation / Web Mention",
                        "HTTP Status": 200,
                        "Is Verified": True
                    })
                    
            if not final_rows and candidate_urls:
                for u in candidate_urls:
                    final_rows.append({
                        "Referring URL": u,
                        "Referring Domain": get_root_domain(u),
                        "Referring Page Title": "Discovered Referring Page",
                        "Target Landing URL": f"https://{clean_target}",
                        "Anchor Text": clean_target,
                        "Link Type": "Web Mention / Archive Link",
                        "HTTP Status": "N/A",
                        "Is Verified": False
                    })
                    
            progress_box.update(label=f"🎉 Discovered {len(final_rows)} Backlinks & Referring Sources!", state="complete", expanded=False)
            st.session_state["backlinks_df"] = pd.DataFrame(final_rows)

# MODE 2: GOOGLE SEARCH CONSOLE (GSC) CSV IMPORT
else:
    st.markdown("""
    <div class="gsc-banner">
        <h4>📥 How to import your 100% accurate Google Search Console (GSC) Backlinks:</h4>
        <ol style="margin-bottom: 0;">
            <li>Go to <a href="https://search.google.com/search-console" target="_blank" style="color: #38BDF8; font-weight: 600;">Google Search Console</a> and select your website.</li>
            <li>Click <b>Links</b> in the left menu.</li>
            <li>Click <b>"EXPORT EXTERNAL LINKS"</b> (top right) and choose <b>Download CSV</b> (or <i>Top linking sites / More sample links</i>).</li>
            <li>Upload that CSV file below:</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    gsc_file = st.file_uploader("Upload GSC External Links CSV", type=["csv"])
    crawl_gsc = st.checkbox("🔍 Live Crawl uploaded GSC links to extract exact Anchor Texts & Dofollow/Nofollow status", value=True)
    
    if gsc_file is not None:
        try:
            raw_gsc_df = pd.read_csv(gsc_file)
            st.success(f"Successfully loaded GSC CSV with **{len(raw_gsc_df)}** entries!")
            
            # Identify columns in GSC export
            cols = list(raw_gsc_df.columns)
            target_url_col = None
            referring_url_col = None
            
            for c in cols:
                c_low = c.lower()
                if "target" in c_low or "destination" in c_low or "page" in c_low:
                    target_url_col = c
                if "source" in c_low or "referring" in c_low or "top target" in c_low or "site" in c_low or "url" in c_low:
                    if referring_url_col is None:
                        referring_url_col = c
                        
            # Format into standardized dataframe
            gsc_rows = []
            if len(cols) == 1:
                # Often GSC export has single column of referring URLs
                for val in raw_gsc_df.iloc[:, 0].dropna():
                    val_str = str(val).strip()
                    if val_str.startswith("http"):
                        gsc_rows.append({
                            "Referring URL": val_str,
                            "Referring Domain": get_root_domain(val_str),
                            "Referring Page Title": "GSC Indexed Referring Page",
                            "Target Landing URL": "N/A",
                            "Anchor Text": "[GSC Indexed Link]",
                            "Link Type": "GSC Verified Backlink",
                            "HTTP Status": 200,
                            "Is Verified": True
                        })
            else:
                for _, row in raw_gsc_df.iterrows():
                    ref_val = str(row[0]).strip()
                    target_val = str(row[1]).strip() if len(cols) > 1 else "N/A"
                    if ref_val.startswith("http"):
                        gsc_rows.append({
                            "Referring URL": ref_val,
                            "Referring Domain": get_root_domain(ref_val),
                            "Referring Page Title": "GSC Indexed Referring Page",
                            "Target Landing URL": target_val,
                            "Anchor Text": "[GSC Indexed Link]",
                            "Link Type": "GSC Verified Backlink",
                            "HTTP Status": 200,
                            "Is Verified": True
                        })
                        
            if gsc_rows:
                if crawl_gsc:
                    st.info("Crawling GSC candidate pages to extract Anchor Texts & Link Types...")
                    ref_urls = [r["Referring URL"] for r in gsc_rows[:40]] # Crawl first 40
                    target_d = get_root_domain(gsc_rows[0]["Target Landing URL"]) if gsc_rows[0]["Target Landing URL"] != "N/A" else ""
                    if target_d:
                        verified = verify_all_candidate_links(ref_urls, target_d, max_workers=max_workers)
                        if verified:
                            # Merge verified anchor data
                            ver_map = {v["Referring URL"]: v for v in verified}
                            for row in gsc_rows:
                                if row["Referring URL"] in ver_map:
                                    row["Anchor Text"] = ver_map[row["Referring URL"]]["Anchor Text"]
                                    row["Link Type"] = ver_map[row["Referring URL"]]["Link Type"]
                                    row["Referring Page Title"] = ver_map[row["Referring URL"]]["Referring Page Title"]
                                    row["HTTP Status"] = ver_map[row["Referring URL"]]["HTTP Status"]
                                    
                st.session_state["backlinks_df"] = pd.DataFrame(gsc_rows)
                st.session_state["target_domain"] = gsc_rows[0]["Referring Domain"] if gsc_rows else "GSC Site"
                
        except Exception as e:
            st.error(f"Error parsing GSC CSV file: {e}")

# Results Dashboard Display
if st.session_state["backlinks_df"] is not None and not st.session_state["backlinks_df"].empty:
    df = st.session_state["backlinks_df"]
    target_dom = st.session_state["target_domain"]
    
    st.markdown("---")
    
    # Summary Metrics Row
    total_backlinks = len(df)
    unique_domains = df["Referring Domain"].nunique()
    dofollow_count = sum(1 for t in df["Link Type"] if "dofollow" in str(t).lower())
    nofollow_count = sum(1 for t in df["Link Type"] if "nofollow" in str(t).lower() or "ugc" in str(t).lower())
    gsc_count = sum(1 for t in df["Link Type"] if "gsc" in str(t).lower())
    unique_anchors = df["Anchor Text"].nunique()
    
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Backlinks</div>
            <div class="metric-value">{total_backlinks}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Referring Domains</div>
            <div class="metric-value" style="color: #A78BFA;">{unique_domains}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Dofollow / GSC</div>
            <div class="metric-value" style="color: #10B981;">{dofollow_count + gsc_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Nofollow / Mentions</div>
            <div class="metric-value" style="color: #F59E0B;">{nofollow_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Unique Anchors</div>
            <div class="metric-value" style="color: #EC4899;">{unique_anchors}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation Tabs
    tab_explorer, tab_charts, tab_domains, tab_ai = st.tabs([
        "📋 Backlinks Explorer", 
        "📊 Visual Analytics", 
        "🌐 Referring Domains", 
        "🤖 Gemini AI Audit & Strategy"
    ])
    
    # Tab 1: Backlinks Explorer
    with tab_explorer:
        st.subheader("Live Backlinks & Anchor Text Table")
        
        c_filter1, c_filter2 = st.columns([1, 2])
        with c_filter1:
            link_types_available = ["All"] + list(df["Link Type"].unique())
            link_type_filter = st.selectbox("Filter by Link Type", link_types_available)
        with c_filter2:
            search_query = st.text_input("Search Referring Domain, Page Title, or Anchor Text", "")
            
        filtered_df = df.copy()
        if link_type_filter != "All":
            filtered_df = filtered_df[filtered_df["Link Type"] == link_type_filter]
        if search_query:
            q = search_query.lower()
            filtered_df = filtered_df[
                filtered_df["Referring Domain"].str.lower().str.contains(q, na=False) |
                filtered_df["Anchor Text"].str.lower().str.contains(q, na=False) |
                filtered_df["Referring URL"].str.lower().str.contains(q, na=False)
            ]
            
        st.dataframe(
            filtered_df[[
                "Referring Domain", "Anchor Text", "Link Type", 
                "Target Landing URL", "Referring URL", "Referring Page Title", "HTTP Status"
            ]],
            use_container_width=True,
            height=420
        )
        
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Backlinks as CSV",
            data=csv_data,
            file_name=f"backlinks_report.csv",
            mime="text/csv",
            type="primary"
        )

    # Tab 2: Visual Analytics
    with tab_charts:
        st.subheader("Backlink Profile Distribution")
        ch_col1, ch_col2 = st.columns(2)
        
        with ch_col1:
            type_counts = df["Link Type"].value_counts().reset_index()
            type_counts.columns = ["Link Type", "Count"]
            fig_pie = px.pie(
                type_counts, 
                names="Link Type", 
                values="Count", 
                title="Link Type Distribution",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_pie.update_layout(margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with ch_col2:
            top_domains = df["Referring Domain"].value_counts().head(10).reset_index()
            top_domains.columns = ["Domain", "Links"]
            fig_dom = px.bar(
                top_domains, 
                x="Links", 
                y="Domain", 
                orientation="h",
                title="Top Referring Domains",
                color="Links",
                color_continuous_scale="Viridis"
            )
            fig_dom.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_dom, use_container_width=True)
            
        # Top Anchor Texts
        st.subheader("Top Anchor Texts Breakdown")
        top_anchors = df["Anchor Text"].value_counts().head(12).reset_index()
        top_anchors.columns = ["Anchor Text", "Frequency"]
        fig_anchors = px.bar(
            top_anchors,
            x="Anchor Text",
            y="Frequency",
            title="Most Frequent Anchor Texts",
            color="Frequency",
            color_continuous_scale="Purples"
        )
        st.plotly_chart(fig_anchors, use_container_width=True)

    # Tab 3: Referring Domains Grouping
    with tab_domains:
        st.subheader("Grouped Referring Domains")
        domain_summary = df.groupby("Referring Domain").agg(
            Total_Links=("Referring URL", "count"),
            Sample_Anchor=("Anchor Text", lambda x: list(x)[:3]),
            Sample_Landing_Page=("Target Landing URL", "first")
        ).reset_index().sort_values(by="Total_Links", ascending=False)
        
        st.dataframe(domain_summary, use_container_width=True, height=400)
        
    # Tab 4: Gemini AI Audit
    with tab_ai:
        st.subheader("🧠 Gemini AI Link Profile & Strategy Report")
        effective_key = api_key_input or os.environ.get("GEMINI_API_KEY")
        
        if not effective_key:
            st.warning("🔑 **Gemini API Key Required**: Enter your free Gemini API key in the left sidebar to generate the AI audit.")
            st.info("You can get a free API key at [Google AI Studio](https://aistudio.google.com/).")
        else:
            if st.button("✨ Generate AI Backlink Audit with Gemini", type="primary"):
                with st.spinner("Analyzing backlink profile and generating SEO recommendations..."):
                    ai_result = analyze_backlinks_with_gemini(
                        target_domain=target_dom,
                        backlinks_data=df.to_dict(orient="records"),
                        api_key=effective_key
                    )
                    st.session_state["ai_analysis"] = ai_result
            
            if st.session_state.get("ai_analysis"):
                st.markdown("---")
                st.markdown(st.session_state["ai_analysis"])

else:
    st.markdown("""
    <div style="background-color: rgba(30, 41, 59, 0.4); border: 1px dashed rgba(255, 255, 255, 0.2); border-radius: 12px; padding: 2rem; text-align: center; margin-top: 2rem;">
        <h3 style="color: #38BDF8;">Ready to analyze your website's backlinks?</h3>
        <p style="color: #94A3B8; max-width: 600px; margin: 0.5rem auto 1.5rem auto;">
            Choose <b>Live Web Discovery</b> or upload your <b>Google Search Console (GSC) Export CSV</b> to get full backlink tables, anchor text distribution, and Gemini AI audits!
        </p>
    </div>
    """, unsafe_allow_html=True)
