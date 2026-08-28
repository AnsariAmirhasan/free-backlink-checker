# 🔗 Free SEO Backlink Checker & Referring Domain Analyzer

A 100% Free, modern SEO tool built with **Python & Streamlit** that uncovers backlinks, referring domains, anchor text, and link types (Dofollow / Nofollow) without needing paid subscriptions to Ahrefs or Semrush. Also integrates **Google Gemini AI** for link profile audits and strategy insights.

---

## ✨ Features

- 🔍 **Multi-Source Free Backlink Discovery**: Queries open web indices, search engine footprints, HackerTarget API, AlienVault OTX, and URLScan.
- 🎯 **Live Link & Anchor Text Extraction**: Multi-threaded crawler inspects candidate pages to extract exact anchor text, target landing URL, and link type (`Dofollow`, `Nofollow`, `UGC`, `Sponsored`).
- 📊 **Visual Analytics**: Interactive Plotly charts for link distribution, top referring domains, and top anchor texts.
- 🧠 **Gemini AI Link Audit**: Analyzes anchor text toxicity, spam risk assessment, and provides actionable outreach strategies.
- 📥 **CSV Export**: 1-click download of all backlink data for reporting in Excel / Google Sheets.
- 🚀 **100% Free & Cloud Deployable**: Ready for 1-click deployment on GitHub & Streamlit Community Cloud.

---

## 🚀 How to Run Locally

### 1. Clone or Open the Project
```bash
cd free-backlink-checker
```

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Setup Gemini API Key
Create a `.env` file:
```bash
cp .env.example .env
```
Add your free Gemini API key from [Google AI Studio](https://aistudio.google.com/):
```env
GEMINI_API_KEY=your_actual_gemini_key_here
```

### 5. Run the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🌐 How to Deploy to GitHub & Streamlit Cloud (Free)

### Step 1: Push Code to GitHub
1. Initialize Git repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Free SEO Backlink Checker"
   ```
2. Create a new repository on [GitHub.com](https://github.com/new) (e.g. `free-backlink-checker`).
3. Push to your repository:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/free-backlink-checker.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Community Cloud (Free)
1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
2. Click **"New app"**.
3. Select your repository: `YOUR_USERNAME/free-backlink-checker`.
4. Main file path: `app.py`.
5. *(Optional for Gemini AI)* Click **"Advanced settings"** -> **"Secrets"** and add:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key"
   ```
6. Click **"Deploy!"** 🚀

Your app will be live on a public URL (e.g. `https://free-backlink-checker.streamlit.app`)!
