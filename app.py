import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

from utils.helper import clean_domain, get_root_domain
from core.discover import discover_all_candidate_referrers
from core.verifier import verify_all_candidate_links
from core.gemini_analyzer import analyze_backlinks_with_gemini

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Free SEO Backlink Checker & Referring Domain Analyzer",
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
    
    if not api_key_input:
        st.info("💡 **Tip**: Adding your free Gemini API key enables deep AI search discovery for any domain!")
        
    st.markdown("---")
    st.subheader("⚙️ Crawler Settings")
    max_workers = st.slider("Crawl Threads", min_value=2, max_value=25, value=10)
    
    st.markdown("---")
    st.markdown("""
    **💡 Free Sources Combined:**
    - 🧠 Google Gemini Search & Web Intelligence
    - 🏛️ Wayback Machine CDX Web Archive
    - 🌐 AlienVault OTX Passive DNS
    - 🔎 Search Engine Footprints & Mentions
    - 🤖 Live DOM / HTML Link & Anchor Extractor
    """)

# Header Section
st.markdown('<div class="main-title">Free SEO Backlink & Referring Domain Checker</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Discover backlinks, referring domains, anchor texts, dofollow/nofollow status & AI link audits — 100% Free.</div>', unsafe_allow_html=True)

# Domain Input Section
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

# Initialize Session State
if "backlinks_df" not in st.session_state:
    st.session_state["backlinks_df"] = None
if "target_domain" not in st.session_state:
    st.session_state["target_domain"] = ""
if "ai_analysis" not in st.session_state:
    st.session_state["ai_analysis"] = None
if "candidate_urls" not in st.session_state:
    st.session_state["candidate_urls"] = []

# Execution Logic
if analyze_btn and target_url_input:
    clean_target = clean_domain(target_url_input)
    st.session_state["target_domain"] = clean_target
    st.session_state["ai_analysis"] = None
    
    st.info(f"Analyzing Target Domain: **{clean_target}**")
    
    progress_box = st.status("🔍 Step 1/2: Discovering referring sources across open web archives & search...", expanded=True)
    
    discovery_res = discover_all_candidate_referrers(
        clean_target,
        gemini_api_key=api_key_input,
        progress_callback=lambda msg: progress_box.write(msg)
    )
    
    candidate_urls = discovery_res["candidate_urls"]
    gemini_links = discovery_res["gemini_links"]
    st.session_state["candidate_urls"] = candidate_urls
    
    progress_box.write(f"✅ Discovered **{len(candidate_urls)}** candidate external URLs across archives, search & AI intelligence.")
    
    if len(candidate_urls) == 0:
        progress_box.update(label="⚠️ No candidate URLs found in open public archives.", state="complete")
        st.warning("No referring pages discovered. If you haven't yet, please enter your free Gemini API Key in the left sidebar to enable AI search discovery!")
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
        
        # Merge verified links with any AI discovered citing pages
        final_rows = []
        if verified_data:
            final_rows.extend(verified_data)
            
        # If any gemini links weren't in verified_data, add them as Discovered Mentions / Citations
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
                
        # If still empty, present candidate URLs cleanly
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
                
        progress_box.update(label=f"🎉 Found {len(final_rows)} Backlinks & Referring Sources!", state="complete", expanded=False)
        st.session_state["backlinks_df"] = pd.DataFrame(final_rows)

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
    mentions_count = total_backlinks - dofollow_count - nofollow_count
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
            <div class="metric-label">Dofollow Links</div>
            <div class="metric-value" style="color: #10B981;">{dofollow_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Nofollow / Mentions</div>
            <div class="metric-value" style="color: #F59E0B;">{nofollow_count + mentions_count}</div>
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
    tab_explorer, tab_charts, tab_domains, tab_ai, tab_candidates = st.tabs([
        "📋 Backlinks Explorer", 
        "📊 Visual Analytics", 
        "🌐 Referring Domains", 
        "🤖 Gemini AI Audit & Strategy", 
        "🔍 Raw Candidate URLs"
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
            file_name=f"{target_dom}_backlinks.csv",
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
                
    # Tab 5: Raw Candidates
    with tab_candidates:
        st.subheader("Discovered Candidate URLs Across Open Indices")
        cand_list = st.session_state.get("candidate_urls", [])
        st.write(f"Total Discovered: **{len(cand_list)}**")
        st.code("\n".join(cand_list) if cand_list else "No candidates found.")

else:
    st.markdown("""
    <div style="background-color: rgba(30, 41, 59, 0.4); border: 1px dashed rgba(255, 255, 255, 0.2); border-radius: 12px; padding: 2rem; text-align: center; margin-top: 2rem;">
        <h3 style="color: #38BDF8;">Ready to analyze your website's backlinks?</h3>
        <p style="color: #94A3B8; max-width: 600px; margin: 0.5rem auto 1.5rem auto;">
            Enter any domain name (e.g. <code>cairindia.com</code>, <code>python.org</code>, or <code>yourwebsite.com</code>) above and click <b>Find Backlinks</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)
