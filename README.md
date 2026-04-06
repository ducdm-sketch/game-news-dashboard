# 🎮 Pixon Game News Dashboard

An automated, AI-powered intelligence platform for **Pixon Game Studio** (FPT Corporation) to aggregate, analyze, and distribute mobile gaming industry insights. The system is specifically optimized for **Hyper-casual**, **Hybrid-casual**, and **Casual** gaming trends.

---

## 🚀 Key Features

*   **Automated Intelligence**: Daily crawler monitors top industry sources (Naavik, Gamigion, Mobilegamer.biz, and more).
*   **Bilingual AI Analysis**: Powered by **OpenAI `gpt-5.4-nano`**, generating:
    *   **English (EN)**: Structured insights for the studio database.
    *   **Vietnamese (VN)**: Human-readable narrative and action items for the Hanoi-based team.
*   **Role-Specific Action Items**: Categorizes findings for internal teams: **Game Research**, **UA**, **Monetization**, and **Game Design**.
*   **Smart Multi-Channel Delivery**:
    *   **Web Dashboard**: A high-performance **Next.js 15** interface for deep-dive research.
    *   **Discord Digest**: Instant Vietnamese reports on the studio's communication channel.
*   **Agnostic Asset Management**: Scrapes and hosts original article images on **Cloudflare R2** to ensure 100% dashboard uptime.
*   **Daily Scheduling**: Automatic execution via **GitHub Actions** at 08:00 Hanoi Time (01:00 UTC).

---

## 🏗️ Architecture & Stack

The platform is split into two core modules:

### 1. The Crawler (`/crawler`)
A Python-based pipeline that executes:
*   **Discovery**: Fetches articles from RSS/Substack/Homepage based on `config/sources.json`.
*   **Scraping**: Extracts clean text while removing ads, navbars, and noise.
*   **AI Analyzer**: Leverages the "Pixon Analyst" prompt for bilingual extraction.
*   **Supabase Storage**: Persists analyzed articles and crawl history.

### 2. The Dashboard (`/dashboard`)
A modern web application built with:
*   **Next.js 15** (Server Components & App Router)
*   **Tailwind CSS**
*   **Supabase SDK** for real-time data syncing.

---

## 🛠️ Getting Started

### Prerequisites
*   Python 3.11+
*   Node.js 20+
*   Supabase Account & Cloudflare R2 Bucket

### Setting up the Crawler
1.  Navigate to the crawler folder: `cd crawler`
2.  Install dependencies: `pip install -r requirements.txt`
3.  Configure your `.env` file (see Environment Variables).
4.  Run manually: `python main.py`

### Setting up the Dashboard
1.  Navigate to the dashboard folder: `cd dashboard`
2.  Install dependencies: `npm install`
3.  Run the development server: `npm run dev`
4.  Open [http://localhost:3000](http://localhost:3000)

---

## 🔧 Environment Variables

A `.env` file is required in both the root and `dashboard/` directories with the following keys:

| Variable | Description |
| :--- | :--- |
| `OPENAI_API_KEY` | OpenAI API Key for `gpt-5.4-nano` |
| `SUPABASE_URL` | Your Supabase Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key for crawler write-access |
| `SUPABASE_PUBLISHABLE_KEY` | Public key for dashboard read-access |
| `DISCORD_WEBHOOK_URL` | Webhook URL for the Vietnamese daily digest |
| `R2_ENDPOINT_URL` | Cloudflare R2 S3 Endpoint |
| `R2_ACCESS_KEY_ID` | R2 Bucket Access Key |
| `R2_SECRET_ACCESS_KEY` | R2 Bucket Secret Key |
| `R2_BUCKET_NAME` | Name of your R2 bucket |
| `R2_PUBLIC_URL` | Public URL for hosted images |

---

## 📦 Deployment

This project is configured to run automatically via **GitHub Actions** (`.github/workflows/crawl.yml`). To enable automation:
1.  Push the code to GitHub.
2.  Add all the **Environment Variables** above to **GitHub Repository Secrets**.
3.  The crawler will run daily at **01:00 UTC**.

---

© 2026 **Pixon Game Studio** | Hanoi, Vietnam.
