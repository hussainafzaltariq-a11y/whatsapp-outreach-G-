# 💬 WhatsApp Outreach Message Generator

A production-ready Streamlit web app that generates personalized WhatsApp outreach messages for business leads — either **for free** using local templates, or with **AI (OpenAI GPT-3.5-turbo)** for higher-quality, unique messages. Built for non-technical users: robust validation, batch processing, cost tracking, and one-click exports.

**🔗 Live Demo:** _[add your deployed Streamlit Cloud / Hugging Face Spaces link here]_

**📸 Screenshots:** _[add screenshots of the Batch, Single Lead, and Analytics tabs here]_

---

## ✨ Features

- **Two generation modes**
  - 🆓 **Template Based** — instant, free, no API key required
  - 🤖 **AI Powered** — OpenAI GPT-3.5-turbo, with automatic fallback to templates if the API call ever fails
- **Batch mode** — upload a CSV of up to 100 leads, generate messages with a live progress bar
- **Single lead mode** — generate one message from manually entered details
- **Robust validation** — CSV structure checks, API key format checks, input sanitization; the app is designed to never crash on bad input
- **Cost tracking** — per-message token/cost breakdown, running session total, CSV usage log, and a monthly cost estimator
- **Exports** — download individual messages as `.txt`, or the full batch as `.csv` / `.txt`
- **Clean WhatsApp-green UI** — tabs for Batch / Single / Analytics, live cost display in the sidebar
- **Modular codebase** — generation logic, cost tracking, and validation are split into separate modules so client change requests are easy to implement

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io) |
| AI generation | [OpenAI API](https://platform.openai.com) (gpt-3.5-turbo) |
| Data handling | Pandas |
| Token counting | tiktoken |
| Charts (optional) | Plotly |

---

## 📁 Project Structure

```
whatsapp-outreach-generator/
├── app.py                  # Main Streamlit app
├── message_generator.py    # AI + template generation, with cost tracking
├── cost_tracker.py         # Token counting, cost calculation, usage logging
├── utils/
│   ├── __init__.py
│   ├── csv_handler.py      # CSV reading & validation
│   ├── templates.py        # Free message templates
│   └── validators.py       # Input validation & sanitization
├── logs/                   # Usage log CSV is written here at runtime
├── requirements.txt
├── packages.txt            # For Streamlit Cloud (not needed for this pure-Python app)
├── sample_leads.csv        # 10-row example batch file
├── .streamlit/
│   └── secrets.toml        # Template for your OpenAI API key
└── README.md
```

---

## 🚀 Installation (Local)

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/whatsapp-outreach-generator.git
   cd whatsapp-outreach-generator
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Add your OpenAI API key for local testing**
   Edit `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "sk-your-real-key-here"
   ```
   This step is optional — you can also just paste your key directly into the sidebar at runtime. Template mode requires no key at all.

5. **Run the app**
   ```bash
   streamlit run app.py
   ```
   The app will open at `http://localhost:8501`.

---

## 📖 Usage Guide

### Batch Processing
1. Go to the **📁 Batch Processing** tab.
2. Download the sample CSV to see the expected format, or prepare your own with columns: `business_name`, `business_type`, `pain_point`, `contact_name`.
3. Upload your CSV (max 100 leads).
4. Review the preview, then click **Generate Messages**.
5. Watch the progress bar, then filter/search results and export as CSV or TXT.

### Single Lead
1. Go to the **✏️ Single Lead** tab.
2. Fill in the four required fields.
3. Click **Generate Single Message** and download the result.

### Analytics
1. Go to the **📊 Analytics** tab to see session totals, a monthly cost calculator, and the full usage history log (AI mode only).

### Switching modes
Use the sidebar radio button to switch between **Template Based (Free)** and **AI Powered (OpenAI)** at any time. In AI mode, paste your API key and click **Test Connection** before generating — if the connection fails or the key is invalid, the app automatically falls back to free templates so you're never blocked.

---

## 💰 Monthly Cost Estimates

Estimates below assume **gpt-3.5-turbo** pricing of **$0.0015 / 1K input tokens** and **$0.002 / 1K output tokens**, and an average of ~200 input tokens + ~150 output tokens per message (~$0.0006/message). Actual cost varies with message length and pain-point detail — check the **Analytics** tab for your real session average, and always verify current pricing at [openai.com/pricing](https://openai.com/pricing).

| Usage Level | Leads/Day | Working Days/Month | Est. Monthly Tokens | Est. Monthly Cost |
|---|---|---|---|---|
| Light | 10 | 22 | ~77,000 | **~$0.13** |
| Moderate | 50 | 22 | ~385,000 | **~$0.66** |
| Heavy | 100 | 22 | ~770,000 | **~$1.32** |

> Template mode is **always $0.00** regardless of volume, since it doesn't call the OpenAI API.

You can recalculate this for your own expected volume anytime in the **Analytics → Monthly Cost Estimator** section — it uses your live session averages once you've generated a few AI messages.

---

## ☁️ Deployment Instructions

### 1. Push to a public GitHub repository
```bash
cd whatsapp-outreach-generator
git init
git add .
git commit -m "Initial commit: WhatsApp Outreach Message Generator"
git branch -M main
git remote add origin https://github.com/<your-username>/whatsapp-outreach-generator.git
git push -u origin main
```
⚠️ **Never commit a real API key.** Make sure `.streamlit/secrets.toml` only contains the placeholder before pushing, and consider adding it to `.gitignore` once you fill in a real key locally.

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**, select your repository, branch (`main`), and set the main file path to `app.py`.
3. Under **Advanced settings → Secrets**, paste:
   ```toml
   OPENAI_API_KEY = "sk-your-real-key-here"
   ```
   (Only needed if you want AI mode to work without users pasting their own key — otherwise leave it out and let each user supply their own key in the sidebar.)
4. Click **Deploy**. Your app will be live at `https://<your-app-name>.streamlit.app`.
5. Update the **Live Demo** link at the top of this README once deployed.

### 3. Alternative: Hugging Face Spaces
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Choose **Streamlit** as the Space SDK.
3. Either upload the project files directly, or connect the Space to your GitHub repo.
4. In **Settings → Repository secrets**, add `OPENAI_API_KEY` if you want a shared key (optional, same caveat as above).
5. The Space will build automatically and serve the app at `https://huggingface.co/spaces/<your-username>/<space-name>`.

---

## 🔧 Handling Client Change Requests

The codebase is intentionally modular so common change requests are quick:

- **New message tone/style** → add an entry to `MESSAGE_TEMPLATES` in `utils/templates.py`.
- **New required CSV column** → update `REQUIRED_CSV_COLUMNS` in `utils/validators.py` and `utils/csv_handler.py`.
- **Different AI model / pricing** → update `model` default and `PRICING` dict in `cost_tracker.py`.
- **New export format** → add a method to `CSVHandler` and a corresponding download button in `app.py`.
- **Branding/theme changes** → edit the `<style>` block at the top of `app.py`.

---

## 📄 License

This project is licensed under the **MIT License** — see below.

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to your branch: `git push origin feature/my-feature`
5. Open a Pull Request describing your change

Bug reports and feature requests are welcome via GitHub Issues.
