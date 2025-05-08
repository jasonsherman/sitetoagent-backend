# 🤖 SiteToAgent – AI-Powered Sales Agent Generator & Knowledge Base Builder

Paste a website URL → Scrape & Summarize → Generate Sales Scripts & Q&A → Download a Branded PDF.

---

## ✨ Project Overview

SiteToAgent is a microservice that transforms any business website into a complete AI sales agent training kit. Instantly scrape, analyze, and summarize a site, then generate:
- A downloadable knowledge base PDF
- 5 branded greeting scripts
- 4 foundational sales Q&A answers

Perfect for chatbot onboarding, sales team training, or rapid business analysis.

---

## 💡 Why I Built This

Most businesses struggle to quickly train AI sales agents on their unique value. I wanted a **simple**, **open-source**, **AI-powered** tool that:
- Automates knowledge extraction from any website
- Delivers ready-to-use sales content
- Makes onboarding and sales enablement effortless

---

## ⚙️ Key Features

- 🌐 Provide any business website URL
- 🤖 AI-powered content summarization (business, services, tone, USPs)
- 💬 Generates 5 branded greeting scripts
- ❓ Auto-answers 4 foundational sales questions
- 📄 Exports a clean, professional knowledge base PDF
- 📦 Download as PDF, TXT/Markdown, or JSON (for chatbot integration)
- 🛡️ No long-term storage: Data is processed in-memory only

---

## 🛠️ Tech Stack

- **Backend:** Python Flask
- **AI Layer:** OpenRouter API

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/jasonsherman/sitetoagent-backend
cd sitetoagent-backend
```

### 2. Backend Setup

#### Create Environment File
Create a `.env` file in the root directory and add your OpenRouter API key:
```bash
OPENROUTER_API_KEY=your_api_key_here
```

#### Set Up Python Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
pip install -r requirements.txt
```
---

## 🔐 Privacy and Security

- No user data or website content is stored long-term.
- All processing is done in-memory for privacy.
- No analytics or tracking by default.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Contributions Welcome!

Open issues, suggest features, or submit pull requests. Let's make AI-powered sales enablement accessible to everyone!

*Made with ❤️ by [Jason Sherman](https://jasonsherman.org) and contributors.* 