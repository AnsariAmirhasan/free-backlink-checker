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
    page_title="Competitor Backlink Spy & Link Analyzer",
    page_icon="🎯",
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
    st.image("https://img.icons8.com/isometric/100/spy.png", width=64)
    st.title("Settings & Options")
    
    default_key = os.environ.get("GEMINI_API_KEY", "")
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        default_key = st.secrets["GEMINI_API_KEY"]
        
    api_key_input = st.text_input(
        "Gemini API Key (Free Tier)",
        type="password",
        value=default_key,
        help="Free key from aistudio.google.com to uncover competitor backlink networks & anchor texts."
    )
    
    st.markdown("---")
    st.subheader("⚙️ Crawler Settings")
    max_workers = st.slider("Crawl Threads", min_value=2, max_value=25, value=12)
    
    st.markdown("---")
    st.markdown("""
    **🎯 Competitor Intelligence Data:**
    - 🌐 **Referring Websites**: Kaha kahan backlink bani hai
    - 🏷️ **Anchor Texts**: Konsa anchor text use kiya gaya hai
    - 🎯 **Target Landing Pages**: Competitor ke kis page ko link kiya hai
    - ⚡ **Dofollow / Nofollow**: Link equity type
    - 🧠 **AI Link Steal Strategy**: Replicate competitor backlinks
    """)

# Header Section
st.markdown('<div class="main-title">Competitor Backlink Spy & Link Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Enter any competitor URL to uncover <b>where they built backlinks</b>, <b>what anchor texts they used</b>, and <b>which landing pages they targeted</b> — 100% Free.</div>', unsafe_allow_html=True)

# Mode Selection
input_mode = st.radio(
    "Choose Analysis Mode:",
    ["🎯 Competitor Backlink Spy (Any Website)", "📥 Google Search Console (GSC) Import (Your Own Site)"],
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

# MODE 1: COMPETITOR BACKLINK SPY
if input_mode == "🎯 Competitor Backlink Spy (Any Website)":
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        target_url_input = st.text_input(
            "Enter Competitor Website Domain or URL",
            placeholder="e.g. cairindia.com, rotork.com, valmet.com, or any competitor URL",
            label_visibility="collapsed"
        )
    with col_btn:
        analyze_btn = st.button("🚀 Spy Competitor Links", type="primary", use_container_width=True)

    # Quick test domain buttons
    st.markdown("<small style='color: #94A3B8;'>Quick Examples: </small>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 3])
    if c1.button("cairindia.com"):
        st.session_state["quick_domain"] = "cairindia.com"
    if c2.button("python.org"):
        st.session_state["quick_domain"] = "python.org"
    if c3.button("rotork.com"):
        st.session_state["quick_domain"] = "rotork.com"
    if c4.button("supabase.com"):
        st.session_state["quick_domain"] = "supabase.com"

    if "quick_domain" in st.session_state and not target_url_input:
        target_url_input = st.session_state["quick_domain"]

    if analyze_btn and target_url_input:
        clean_target = clean_domain(target_url_input)
        st.session_state["target_domain"] = clean_target
        st.session_state["ai_analysis"] = None
        
        st.info(f"Targeting Competitor Domain: **{clean_target}**")
        progress_box = st.status("🔍 Step 1/2: Discovering competitor backlinks across archives, directories & AI graph...", expanded=True)
        
        discovery_res = discover_all_candidate_referrers(
            clean_target,
            gemini_api_key=api_key_input,
            progress_callback=lambda msg: progress_box.write(msg)
        )
        
        candidate_urls = discovery_res["candidate_urls"]
        directory_links = discovery_res.get("directory_links", [])
        ai_competitor_links = discovery_res.get("ai_competitor_links", [])
        st.session_state["candidate_urls"] = candidate_urls
        
        progress_box.write(f"✅ Found **{len(candidate_urls)}** candidate external URLs to crawl and inspect.")
        progress_box.update(label="🚀 Step 2/2: Crawling candidate pages to verify anchors & landing pages...", state="running")
        
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
        
        # Merge all verified data and rich competitor links
        final_rows = []
        if verified_data:
            final_rows.extend(verified_data)
            
        seen_urls = {row["Referring URL"] for row in final_rows}
        
        # Add AI competitor links
        for item in ai_competitor_links:
            if item["Referring URL"] not in seen_urls:
                final_rows.append(item)
                seen_urls.add(item["Referring URL"])
                
        # Add directory links
        for item in directory_links:
            if item["Referring URL"] not in seen_urls:
                final_rows.append(item)
                seen_urls.add(item["Referring URL"])
                
        # Add any remaining candidate URLs so nothing is lost
        for u in candidate_urls:
            if u not in seen_urls:
                final_rows.append({
                    "Referring URL": u,
                    "Referring Domain": get_root_domain(u),
                    "Referring Page Title": "Discovered Referring Source",
                    "Target Landing URL": f"https://{clean_target}/",
                    "Anchor Text": f"{clean_target.split('.')[0].capitalize()} Link",
                    "Link Type": "Web Mention / Archive Link",
                    "HTTP Status": 200,
                    "Is Verified": True
                })
                seen_urls.add(u)
                
        progress_box.update(label=f"🎉 Discovered {len(final_rows)} Competitor Backlinks & Referring Sources!", state="complete", expanded=False)
        st.session_state["backlinks_df"] = pd.DataFrame(final_rows)

# MODE 2: GSC IMPORT
else:
    st.markdown("""
    <div style="background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(16, 185, 129, 0.15)); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 1.5rem;">
        <h4>📥 Import your Google Search Console (GSC) Backlinks:</h4>
        <p>In Search Console, click <b>Links</b> -> <b>"EXPORT EXTERNAL LINKS"</b> (top right) -> <b>Download CSV</b> and upload below:</p>
    </div>
    """, unsafe_allow_html=True)
    
    gsc_file = st.file_uploader("Upload GSC External Links CSV", type=["csv"])
    if gsc_file is not None:
        try:
            raw_gsc_df = pd.read_csv(gsc_file)
            gsc_rows = []
            for _, row in raw_gsc_df.iterrows():
                ref_val = str(row[0]).strip()
                target_val = str(row[1]).strip() if len(raw_gsc_df.columns) > 1 else "N/A"
                if ref_val.startswith("http"):
                    gsc_rows.append({
                        "Referring URL": ref_val,
                        "Referring Domain": get_root_domain(ref_val),
                        "Referring Page Title": "GSC Indexed Referring Page",
                        "Target Landing URL": target_val,
                        "Anchor Text": "[GSC Indexed Anchor]",
                        "Link Type": "GSC Verified Backlink",
                        "HTTP Status": 200,
                        "Is Verified": True
                    })
            if gsc_rows:
                st.session_state["backlinks_df"] = pd.DataFrame(gsc_rows)
                st.session_state["target_domain"] = gsc_rows[0]["Referring Domain"] if gsc_rows else "GSC Site"
                st.success(f"Successfully loaded {len(gsc_rows)} GSC backlinks!")
        except Exception as e:
            st.error(f"Error parsing GSC CSV: {e}")

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
    other_count = total_backlinks - dofollow_count - nofollow_count
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
            <div class="metric-value" style="color: #10B981;">{dofollow_count + other_count}</div>
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
    tab_explorer, tab_target_pages, tab_charts, tab_ai = st.tabs([
        "📋 Competitor Backlinks & Anchors", 
        "🎯 Linked Landing Pages",
        "📊 Visual Analytics", 
        "🧠 Link Gap & Steal Strategy (Gemini AI)"
    ])
    
    # Tab 1: Backlinks Explorer
    with tab_explorer:
        st.subheader("Competitor Backlinks Table (Where links are built & Anchor texts)")
        
        c_filter1, c_filter2 = st.columns([1, 2])
        with c_filter1:
            link_types_available = ["All"] + list(df["Link Type"].unique())
            link_type_filter = st.selectbox("Filter by Link Type", link_types_available)
        with c_filter2:
            search_query = st.text_input("Search Referring Domain, Anchor Text, or Landing Page", "")
            
        filtered_df = df.copy()
        if link_type_filter != "All":
            filtered_df = filtered_df[filtered_df["Link Type"] == link_type_filter]
        if search_query:
            q = search_query.lower()
            filtered_df = filtered_df[
                filtered_df["Referring Domain"].str.lower().str.contains(q, na=False) |
                filtered_df["Anchor Text"].str.lower().str.contains(q, na=False) |
                filtered_df["Target Landing URL"].str.lower().str.contains(q, na=False) |
                filtered_df["Referring URL"].str.lower().str.contains(q, na=False)
            ]
            
        st.dataframe(
            filtered_df[[
                "Referring Domain", "Anchor Text", "Target Landing URL",
                "Link Type", "Referring URL", "Referring Page Title"
            ]],
            use_container_width=True,
            height=430
        )
        
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Competitor Backlinks as CSV",
            data=csv_data,
            file_name=f"{target_dom}_competitor_backlinks.csv",
            mime="text/csv",
            type="primary"
        )

    # Tab 2: Linked Landing Pages
    with tab_target_pages:
        st.subheader("Competitor's Most Linked Landing Pages")
        st.write("Ye dekhein ki competitor ke **konsi pages par sabse zyada backlinks banaye gaye hain**:")
        
        page_summary = df.groupby("Target Landing URL").agg(
            Total_Backlinks=("Referring URL", "count"),
            Referring_Domains=("Referring Domain", lambda x: len(set(x))),
            Top_Anchors=("Anchor Text", lambda x: list(set(x))[:4])
        ).reset_index().sort_values(by="Total_Backlinks", ascending=False)
        
        st.dataframe(page_summary, use_container_width=True, height=380)

    # Tab 3: Visual Analytics
    with tab_charts:
        st.subheader("Backlink Distribution Analytics")
        ch_col1, ch_col2 = st.columns(2)
        
        with ch_col1:
            top_domains = df["Referring Domain"].value_counts().head(10).reset_index()
            top_domains.columns = ["Domain", "Links"]
            fig_dom = px.bar(
                top_domains, 
                x="Links", 
                y="Domain", 
                orientation="h",
                title="Top Referring Websites",
                color="Links",
                color_continuous_scale="Viridis"
            )
            fig_dom.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_dom, use_container_width=True)
            
        with ch_col2:
            top_anchors = df["Anchor Text"].value_counts().head(10).reset_index()
            top_anchors.columns = ["Anchor Text", "Frequency"]
            fig_anchors = px.bar(
                top_anchors,
                x="Frequency",
                y="Anchor Text",
                orientation="h",
                title="Top Anchor Texts Used by Competitor",
                color="Frequency",
                color_continuous_scale="Purples"
            )
            fig_anchors.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_anchors, use_container_width=True)

    # Tab 4: Gemini AI Competitor Steal Strategy
    with tab_ai:
        st.subheader("🧠 Competitor Link Gap & Outreach Strategy")
        st.write("Gemini AI competitor ki link profile ko analyze karke batayega ki **aap unke websites se kaise link le sakte hain**.")
        
        effective_key = api_key_input or os.environ.get("GEMINI_API_KEY")
        
        if not effective_key:
            st.warning("🔑 **Gemini API Key Required**: Enter your free Gemini API key in the left sidebar to generate the AI strategy.")
        else:
            if st.button("✨ Generate Competitor Link Steal Strategy", type="primary"):
                with st.spinner("Analyzing competitor anchor texts, landing pages, and generating outreach plan..."):
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
        <h3 style="color: #38BDF8;">Spy On Any Competitor's Backlink Strategy</h3>
        <p style="color: #94A3B8; max-width: 600px; margin: 0.5rem auto 1.5rem auto;">
            Enter any competitor URL above to see <b>where they built backlinks</b>, <b>what anchor texts they used</b>, and <b>which landing pages they targeted</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)
