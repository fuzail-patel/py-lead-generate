# 🚀 Lead Generation & Research Workflow — Python + FastAPI

## 🧠 Overview

This project automates **lead research, company profiling, and personalized outreach email generation** using a modular Python architecture.  
It is designed to integrate seamlessly with **n8n**, automation frameworks, or direct HTTP API calls via FastAPI.

---

## ⚙️ Key Features

- 🌐 **Smart Search + Scraping** — Uses DuckDuckGo and web scraping with **SOCKS5 proxy rotation** to avoid IP blocking.  
- 🔄 **Intelligent Proxy System** — Real-world proxy testing against DuckDuckGo with parallel validation and automatic bad proxy marking.
- ⚡ **High Performance** — Optimized scraping with connection pooling, parallel workers, and early content extraction (60% faster).
- 🧹 **Filtering Engine** — Cleans and structures scraped content for AI processing.  
- 🤖 **LLM Integration** — Generates company summaries, proposals, and complete outreach emails using OpenAI (no placeholders).  
- 💌 **Email Formatter** — Creates professional, ready-to-send email templates with automatic sender signatures.  
- 🧱 **Exception-Safe Workflow** — Each stage is modular and error-isolated for debugging and retrying.  
- 🔁 **Auto-Retry Mechanism** — Failed requests automatically retry with different proxies (3 attempts).
- 🧩 **n8n Ready** — Accepts JSON input and produces clean JSON output for automation pipelines.
- 🌐 **FastAPI REST API** — HTTP endpoints for programmatic access with interactive API documentation.  

---

## 🗂️ Project Structure

```
py-lead-generator-main/
│
├─ .env                    # Environment variables
├─ .env.example            # Example env config
├─ proxy_list.csv          # Cached list of public SOCKS5 proxies
├─ run.py                  # Main entry point (used by n8n / local CLI)
├─ run_workflow.py         # Core orchestrator (called by run.py)
├─ run_proxy_extractor.py  # Fetches and validates public proxies
├─ server.py               # FastAPI REST API server
├─ test_input.json         # Sample input payload
│
├─ constants/
│   ├─ config.py           # Configuration constants
│   ├─ prompts.py          # Prompt templates for LLM
│   ├─ proxy.py            # Proxy-related constants and URLs
│   ├─ searchTemplates.py  # Predefined search query formats
│   ├─ userAgents.py       # Randomized User-Agent list
│
├─ modules/
│   ├─ search.py           # Performs search queries (DuckDuckGo)
│   ├─ scrapper.py         # Extracts text content from URLs using rotating proxies
│   ├─ filter.py           # Cleans and preprocesses text
│   ├─ llm.py              # Generates summaries, research, and emails
│   ├─ email.py            # Formats email templates with placeholders
│   ├─ proxy.py            # Manages proxy rotation and validation
│   ├─ main.py             # Initializes all modules (central import layer)
│   └─ exceptions/
│       └─ exceptions.py   # Custom exception classes for modular error handling
│
├─ utils/
│   └─ helpers.py          # Shared utility functions
│
└─ README.md               # This file
```

---

## 🔁 Workflow Pipeline

```
SearchModule  →  ScraperModule  →  FilterModule  →  LLMModule  →  EmailModule
     │                 │                │                 │
     │                 │                │                 │
     └──────────────► WorkflowFacade ◄────────────────────┘
                             │
                             ▼
                      run_workflow()
                             │
                             ▼
                       run.py / server.py
```

---

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Internet connection (for proxy fetching and API calls)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd py-lead-generator-main
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```
   
   **Optional:** Customize sender information:
   ```bash
   SENDER_NAME=Your Name
   SENDER_TITLE=Your Title
   SENDER_COMPANY=Your Company
   SENDER_EMAIL=your@email.com
   SENDER_PHONE=+1234567890
   ```

4. **Initialize proxy list**
   ```bash
   python run_proxy_extractor.py
   ```
   
   This fetches and tests 100+ proxies, saving the top 30 to `proxy_list.csv`.

5. **Test the system**
   ```bash
   # Windows
   Get-Content test_input.json | python run.py
   
   # Linux/Mac
   cat test_input.json | python run.py
   ```

---

## ⚡ Quick Start

### Method 1: CLI Mode (JSON Input)

**Important:** All input must be provided via JSON (stdin). No defaults or environment variables are used for input fields.

```bash
# Windows PowerShell
Get-Content test_input.json | python run.py

# Linux/Mac/WSL
cat test_input.json | python run.py

# Minimal example (only topic required)
echo '{"topic":"Company Name"}' | python run.py
```

### Method 2: FastAPI REST API

```bash
# Start the server
uvicorn server:app --host 0.0.0.0 --port 8000

# Or with auto-reload for development
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Endpoints:** `http://localhost:8000/api/`
- **Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs:** `http://localhost:8000/redoc` (ReDoc)

### Method 3: Docker

```bash
# Build the image
docker build -t py-lead-generator .

# Run the API server
docker run -p 8000:8000 --env-file .env py-lead-generator

# Or run CLI mode
docker run -i --rm --env-file .env py-lead-generator python3 run.py < test_input.json
```

---

## 📋 Input Schema

### Required Fields

Only `topic` is required. All other fields are optional.

```json
{
  "topic": "Company Name or Topic"
}
```

### Complete Input Schema

```json
{
  "topic": "string (required)",
  "mode": "string (optional, default: 'lead')",
  "recipient_name": "string (optional)",
  "sender_company_summary": "string (optional)",
  "max_results": "number (optional, default: 5)",
  "sender_info": {
    "sender_name": "string (optional)",
    "sender_title": "string (optional)",
    "sender_company": "string (optional)",
    "sender_phone": "string (optional)",
    "sender_email": "string (optional)",
    "sender_website": "string (optional)",
    "sender_address": "string (optional)"
  }
}
```

### Field Descriptions

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `topic` | string | **Yes** | - | Company name or research topic (the target company) |
| `mode` | string | No | `"lead"` | Workflow mode: `lead`, `research`, `general` |
| `recipient_name` | string | No | `""` | Name of email recipient (for lead mode) |
| `sender_company_summary` | string | No | `""` | **Description of YOUR company (the sender)** - helps AI write personalized outreach emails mentioning your services. This is NOT about the target company. |
| `max_results` | number | No | `5` | Maximum search results to scrape (1-20) |

**Important:** `sender_company_summary` describes **YOUR company** (the sender), not the target company. The AI uses this to personalize emails by mentioning your services.

### Mode Options

| Mode | Output | Use Case |
|------|--------|----------|
| `lead` | Summary + Email | Lead generation & outreach |
| `research` | Content only | Company research without email |
| `general` | Summary + Content | General information gathering |

### Example Inputs

#### Minimal Lead Generation
```json
{
  "topic": "Stripe Inc"
}
```

#### Complete Lead Generation
```json
{
  "topic": "Stripe Inc",
  "mode": "lead",
  "recipient_name": "Sarah Chen",
  "sender_company_summary": "We are a payment integration consultancy that helps e-commerce businesses optimize their payment workflows and reduce transaction fees.",
  "max_results": 8,
  "sender_info": {
    "sender_name": "Michael Rodriguez",
    "sender_title": "Senior Business Development Manager",
    "sender_company": "CloudSync Solutions",
    "sender_phone": "+1 (555) 234-5678",
    "sender_email": "m.rodriguez@cloudsync.io",
    "sender_website": "https://www.cloudsync.io",
    "sender_address": "350 5th Avenue, Suite 4500, New York, NY 10118"
  }
}
```

#### Research Mode
```json
{
  "topic": "Artificial Intelligence in Healthcare",
  "mode": "research",
  "max_results": 10
}
```

---

## 🌐 FastAPI REST API

### API Endpoint: `/api/generate`

Generate outreach email or research content via HTTP POST.

**Endpoint:** `POST /api/generate`

**Required Fields:**
- `topic` (string): Company name or topic to research (cannot be empty or whitespace)

**Optional Fields:**
- `mode` (string): Workflow mode - `"lead"`, `"general"`, or `"research"` (default: `"lead"`)
- `recipient_name` (string): Name for personalized emails
- `sender_company_summary` (string): **Description of YOUR company (the sender)** - helps AI personalize the email by mentioning your services
- `sender_info` (object): Sender information for email signature
  - `sender_name` (string)
  - `sender_title` (string)
  - `sender_company` (string)
  - `sender_phone` (string)
  - `sender_email` (string)
  - `sender_website` (string)
  - `sender_address` (string)
- `max_results` (integer): Number of search results (1-20, default: 5)

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Stripe Inc",
    "mode": "lead",
    "recipient_name": "John Doe",
    "sender_company_summary": "We are a payment integration consultancy that helps businesses optimize their payment workflows",
    "sender_info": {
      "sender_name": "Jane Smith",
      "sender_email": "jane@example.com",
      "sender_company": "TechCorp"
    }
  }'
```

**Example Response (Lead Mode):**

```json
{
  "success": true,
  "mode": "lead",
  "summary": "Stripe is a payment processing platform...",
  "email": {
    "subject": "Partnership Opportunity with TechCorp",
    "body": "<html>...</html>"
  }
}
```

**Validation:**

The API enforces strict validation:
- ✅ `topic` is required and cannot be empty or whitespace
- ✅ `mode` must be one of: `"lead"`, `"general"`, `"research"`
- ✅ `max_results` must be between 1 and 20
- ✅ Returns HTTP 422 for validation errors
- ✅ Returns HTTP 400 for workflow errors
- ✅ Returns HTTP 500 for internal errors

**Error Response Example:**

```json
{
  "detail": {
    "success": false,
    "error_type": "SearchFailedError",
    "message": "DuckDuckGo returned no valid URLs"
  }
}
```

---

## 🌐 Intelligent Proxy System

DuckDuckGo aggressively blocks scraping. To bypass this, the project uses an **intelligent SOCKS5 proxy system** with automatic retry and bad proxy marking.

### How It Works

1. **Load Proxies** — Reads from `proxy_list.csv` on startup (30 tested proxies)
2. **Smart Selection** — Picks random proxy, excluding previously failed ones
3. **Auto-Retry** — If proxy fails, automatically tries another (up to 3 attempts)
4. **Bad Proxy Marking** — Failed proxies are marked and excluded from future requests
5. **Fallback** — Uses hardcoded proxies from `constants/proxy.py` if CSV missing

### Key Features

- ✅ **Automatic Retry** — Up to 3 attempts with different proxies
- ✅ **Bad Proxy Delisting** — Failed proxies blacklisted during runtime
- ✅ **Persistent Bad Proxy Removal** — Bad proxies are removed from CSV file immediately (won't be used after restart)
- ✅ **Smart Reset** — If all proxies bad, automatically resets and retries
- ✅ **Detailed Logging** — Shows proxy status, attempts, and failures
- ✅ **Fallback Strategy** — Never fails due to missing CSV

### Manual Proxy Refresh

```bash
# Run this manually when you need fresh proxies
python run_proxy_extractor.py

# Output: Writes 30 verified proxies to proxy_list.csv
```

**Recommended:** Refresh proxies daily for high-volume usage, weekly for low-volume.

### Example Logs

```
[SUCCESS] Loaded 30 proxies from proxy_list.csv
[ERROR] Proxy error with socks5://1.2.3.4:1080 (attempt 1/3)
[DELIST] Marked proxy as bad: socks5://1.2.3.4:1080 (1 bad proxies)
[SUCCESS] Request succeeded on attempt 2 with proxy socks5://5.6.7.8:1080
```

---

## ⚡ Performance Optimizations

The project has been optimized for speed and efficiency:

### Scraping Optimizations
- **Connection Pooling** — Reuses HTTP connections via `requests.Session()` to reduce overhead
- **Parallel Scraping** — Uses 10 concurrent workers to scrape multiple pages simultaneously
- **Early Content Extraction** — Stops parsing once 2000 characters of relevant content are found
- **Adaptive Timeouts** — 5s initial timeout with 3s retry for better performance on slow pages
- **Content Length Pre-check** — Skips pages larger than 2MB before downloading
- **Selective HTML Parsing** — Prioritizes main content areas (main, article, .content) first
- **Duplicate Detection** — Set-based O(1) lookup to avoid processing duplicate content
- **Optimized String Operations** — Uses list + join() instead of += for efficient concatenation

### Proxy Optimizations
- **Parallel Testing** — Tests proxies concurrently (30 workers) for 10-20x faster validation
- **Real-World Validation** — Tests against actual DuckDuckGo searches instead of generic IP checks
- **Comprehensive Collection** — Collects all working proxies without early termination

### Results
- **Scraping Time** — Reduced from 60s to 22-25s (60% improvement)
- **Proxy Testing** — Reduced from 1 hour to 5-10 minutes for 1700 proxies
- **Memory Usage** — Reduced through stream-based fetching and early termination

---

## 📊 Output Format

### Success Response (Lead Mode)

```json
{
  "success": true,
  "mode": "lead",
  "summary": "Company summary here...",
  "email": {
    "subject": "Email subject line",
    "body": "<html>...formatted email...</html>"
  }
}
```

### Success Response (Research/General Mode)

```json
{
  "success": true,
  "mode": "research",
  "summary": "Research summary here...",
  "content": "Full scraped and filtered content..."
}
```

### Error Response

```json
{
  "success": false,
  "error_type": "InsufficientContentError",
  "message": "No sufficient content found for topic: 'Company Name'.",
  "topic": "Company Name"
}
```

---

## ⚠️ Error Handling

| Error Type | Description |
|-------------|-------------|
| `ProxyFailureError` | All proxy attempts failed - indicates network/proxy infrastructure issue, NOT a bad lead |
| `SearchFailedError` | Search engine returned no results |
| `InsufficientContentError` | Scraped data insufficient for LLM - indicates the topic/lead has no sufficient content |
| `LLMProcessingError` | LLM failed to generate a valid response |
| `SearchBlockedError` | IP or proxy temporarily blocked |
| `UnknownError` | Any unexpected runtime error |

All errors return JSON with:
- `success: false`
- `error_type`: Type of error
- `message`: Descriptive error message
- `topic`: The topic that caused the error
- `is_infrastructure_error`: (Optional) `true` for infrastructure issues (ProxyFailureError), `false` for content issues

**Important:** `ProxyFailureError` indicates a network/proxy problem, not that the lead is invalid. Use `is_infrastructure_error` to distinguish between infrastructure issues and actual content problems.

---

## 🔌 Integration Examples

### n8n Integration

**Execute Command Node:**
```bash
python3 /path/to/run.py
```

**Expected Flow:**
```
Webhook (lead trigger)
   ↓
Execute Command (run.py)
   ↓
Email Node (send email)
   ↓
MongoDB Node (update lead status)
```

### Python Script

```python
import subprocess
import json

input_data = {
    "topic": "SpaceX",
    "mode": "lead",
    "recipient_name": "Elon Musk",
    "sender_company_summary": "We provide rocket propulsion consulting services"
}

result = subprocess.run(
    ["python", "run.py"],
    input=json.dumps(input_data),
    capture_output=True,
    text=True
)

output = json.loads(result.stdout)
print(output["summary"])
```

### HTTP API Call

```python
import requests

response = requests.post(
    "http://localhost:8000/api/generate",
    json={
        "topic": "Stripe Inc",
        "mode": "lead",
        "recipient_name": "John Doe",
        "sender_company_summary": "We are a payment integration consultancy"
    }
)

result = response.json()
print(result["email"]["subject"])
```

---

## 🔄 Maintenance

### Refreshing Proxies

Proxies should be refreshed periodically (daily or weekly depending on usage):

```bash
python run_proxy_extractor.py
```

This updates `proxy_list.csv` with fresh, tested proxies. The system automatically uses these on the next run.

---

## 🆘 Troubleshooting

### Issue: "OpenAI API key not provided"
**Solution:** Create `.env` file with `OPENAI_API_KEY=sk-...`

### Issue: "No proxies available"
**Solution:** Run `python run_proxy_extractor.py` to fetch proxies

### Issue: Import errors
**Solution:** Run `pip install -r requirements.txt`

### Issue: "[WARNING] Proxy CSV file not found"
**Solution:** Run `python run_proxy_extractor.py` to create `proxy_list.csv`
**Note:** System falls back to hardcoded proxies automatically

### Issue: "Search blocked"
**Solution:** Refresh proxies with `python run_proxy_extractor.py`

### Issue: Docker proxy failures
**Solution:** Ensure `pysocks` or `requests[socks]` is installed. Add to `requirements.txt`:
```txt
requests[socks]>=2.31.0
```

---

## 🧭 Roadmap

- [x] ~~ProxyFailureError exception for better error distinction~~ ✅ Completed in v1.7.0
- [x] ~~Performance optimizations (connection pooling, parallel scraping)~~ ✅ Completed in v1.8.0
- [x] ~~Real-world proxy testing against DuckDuckGo~~ ✅ Completed in v1.8.0
- [ ] Automated proxy refresh scheduling (cron/Docker)
- [ ] Add proxy pool scoring (based on response time & health)
- [ ] Retry system with exponential backoff for failed proxies
- [ ] HTML sanitization & content enrichment
- [ ] Support for Gmail / ZeptoMail sending
- [ ] Batch mode for multi-lead processing
- [ ] Structured logging with colorized output

---

## 📝 Notes

### About Email Generation

The LLM generates **complete, finished emails** with no placeholders:
- ✅ **Complete Emails** — AI generates full email body with proper greeting and content
- ✅ **Natural Recipient Handling** — Uses provided `recipient_name` directly, or professional generic greeting if not provided
- ✅ **No Placeholders** — Never uses placeholders like `[Recipient]`, `[Name]`, etc.
- ✅ **Automatic Signatures** — Always includes "Best regards," with optional sender details

### About `sender_company_summary`

The `sender_company_summary` field describes **YOUR company** (the sender), not the target company:

- ✅ **Correct:** `"We are a payment integration consultancy that helps businesses..."` (describes YOUR company)
- ❌ **Incorrect:** `"Stripe is a payment processing platform..."` (describes the target company)

The AI uses your company summary to personalize outreach emails by naturally mentioning how your services relate to the target company.

---

## 🧾 License

MIT License © 2025 **Xupyter Solutions**

---

## 📚 Additional Resources

- **Sample Input:** See `test_input.json` in the project root
- **API Documentation:** Visit `http://localhost:8000/docs` when server is running
- **Version History:** See `CHANGELOG.md`
