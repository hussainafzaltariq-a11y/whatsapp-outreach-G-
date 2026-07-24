---
title: WhatsApp Outreach Generator
emoji: 💬
colorFrom: green
colorTo: green
sdk: gradio
sdk_version: "6.20.0"
python_version: "3.10"
app_file: app.py
pinned: false
suggested_hardware: "t4-small"
---
Live demo: https://huggingface.co/spaces/Tariq349/Whatsapp-outreach-G

<img width="950" height="478" alt="image" src="https://github.com/user-attachments/assets/a43e3e23-59f3-4708-b476-fa5c64149ec9" />
<img width="938" height="474" alt="image" src="https://github.com/user-attachments/assets/4b7fbcd3-f474-4343-bddb-f64b986b63db" />
<img width="951" height="475" alt="image" src="https://github.com/user-attachments/assets/385b6d24-6b9a-40f2-baba-a81ac71f6d3d" />



# 💬 WhatsApp Outreach Message Generator

A production-ready WhatsApp outreach message generator with **ZeroGPU support** for fast AI-powered message generation.
## ✨ Features

- **Two generation modes**: Template Based (Free) or AI Powered (OpenAI)
- **Batch mode**: Upload CSV of up to 100 leads with live progress bar
- **Single lead mode**: Manually enter details for one message
- **Robust validation**: Never crashes on bad input
- **Cost tracking**: Per-message cost, session totals, monthly estimates
- **Exports**: Download as `.txt`, `.csv`, or full batch export

## 🛠 Tech Stack

- **UI**: Streamlit
- **AI**: OpenAI API (gpt-3.5-turbo)
- **Data**: Pandas
- **Token counting**: tiktoken

## 🚀 Quick Start

1. **Template Mode**: Select in sidebar, no API key needed
2. **AI Mode**: Enter OpenAI API key, click "Test Connection"
3. **Batch Processing**: Upload CSV with columns: `business_name`, `business_type`, `pain_point`, `contact_name`
4. **Single Lead**: Fill in form and generate

## 💰 Monthly Cost Estimates

| Daily Leads | Est. Monthly Cost |
|-------------|-------------------|
| 10 leads/day | ~$0.13 |
| 50 leads/day | ~$0.66 |
| 100 leads/day | ~$1.32 |

*Template mode is always $0.00*

## 📄 License

MIT License
