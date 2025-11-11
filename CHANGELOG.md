# 🧾 Changelog

## [1.8.0] — 2025-01-XX
### Added
- **Real-World Proxy Testing** — Proxy extractor now tests proxies against DuckDuckGo with actual search queries, matching production usage
- **Parallel Proxy Testing** — Proxy extraction uses ThreadPoolExecutor (30 workers) for 10-20x faster validation
- **Comprehensive Proxy Collection** — Removed target limits to collect all working proxies instead of stopping early
- **Connection Pooling** — Scraper uses `requests.Session()` to reuse HTTP connections, reducing overhead
- **Early Content Extraction** — Stops parsing HTML once 2000 characters of relevant content are collected
- **Adaptive Timeouts** — Initial 5s timeout with 3s retry timeout for better performance on slow pages
- **Content Length Pre-check** — Skips pages larger than 2MB before downloading to save bandwidth
- **Selective HTML Parsing** — Prioritized CSS selectors target main content areas first (main, article, .content)
- **Duplicate Content Detection** — Set-based O(1) lookup to avoid processing duplicate text blocks
- **Performance Logging** — Detailed timing logs for DuckDuckGo searches and proxy operations
- **Pydantic V2 Support** — Updated to Pydantic V2 for Python 3.14 compatibility

### Changed
- **Proxy Testing Strategy** — Tests proxies with real DuckDuckGo searches instead of IP-API checks
- **Proxy Validation** — Requires at least 3 search results to validate proxy functionality
- **Email Generation** — LLM now generates complete emails with no placeholders; removed client-side replacement logic
- **Recipient Name Handling** — `recipient_name` is now passed directly to LLM prompt for natural email generation
- **Parallel Scraping** — Increased parallel workers from 5 to 10 for faster page scraping
- **String Concatenation** — Optimized to use list + join() instead of += for better performance
- **Keyword Checking** — Optimized to lowercase text once instead of repeatedly
- **Sender Signature** — Always includes "Best regards," with optional sender details
- **Dependencies** — Updated `pydantic` from `<2.0.0` to `>=2.0.0` in requirements.txt

### Fixed
- **Proxy Reliability** — Proxies are now tested against actual DuckDuckGo usage, eliminating false positives
- **Email Placeholders** — Removed placeholder replacement; LLM generates complete emails directly
- **Missing Sender Closing** — Sender signature now consistently appears in all emails
- **Pydantic Compatibility** — Fixed Pydantic V1/V2 incompatibility with Python 3.14

### Performance
- **Scraping Speed** — Reduced scraping time from 60s to 22-25s (60% improvement)
- **Proxy Testing Speed** — Parallel testing reduces 1-hour sequential tests to ~5-10 minutes
- **Memory Efficiency** — Stream-based content fetching and early termination reduce memory usage
- **Network Efficiency** — Connection pooling and content length checks reduce redundant requests

---

## [1.7.0] — 2025-01-XX
### Added
- **ProxyFailureError Exception** — New exception type to distinguish proxy failures from insufficient content
- **Persistent Bad Proxy Removal** — Bad proxies are now removed from CSV file immediately (persists across restarts)
- **Infrastructure Error Flag** — Error responses include `is_infrastructure_error` flag to distinguish proxy issues from content issues

### Changed
- **Field Rename** — Renamed `company_summary` to `sender_company_summary` for clarity (describes sender's company, not target)
- **Documentation Consolidation** — Consolidated all documentation into README.md and CHANGELOG.md
- **Documentation Clarification** — Clarified that `sender_company_summary` describes the sender's company, not the target company
- **Proxy Failure Handling** — `proxy.fetch()` now raises `ProxyFailureError` instead of returning empty string
- **Error Clarity** — API now returns `ProxyFailureError` for proxy issues vs `InsufficientContentError` for content issues

### Fixed
- **Proxy Failure Misclassification** — Fixed issue where proxy failures were incorrectly reported as `InsufficientContentError`
- **Server Restart Issue** — Bad proxies are now persisted to CSV, so they won't be used after server restart

### Removed
- Removed redundant documentation files (QUICK_START.md, INPUT_SCHEMA.md, API_CHANGES.md, PROXY_SYSTEM.md) - content merged into README.md

---

## [1.6.0] — 2025-11-06
### Added
- **CSV-Based Proxy System** — ProxyManager now reads from `proxy_list.csv` with automatic fallback to constants.
- **Smart Proxy Loading** — Loads fresh proxies on application start with comprehensive error handling.
- **Automatic Retry Mechanism** — Retries failed requests with different proxies (configurable, default: 3 attempts).
- **Bad Proxy Marking** — Failed proxies are automatically marked as bad and excluded from future requests.
- **Proxy Delisting** — `mark_proxy_bad()` method to blacklist failing proxies during runtime.
- **Available Proxy Tracking** — `get_available_proxy_count()` shows good proxies vs total proxies.
- **Proxy Count Tracking** — Added `get_proxy_count()` method to monitor total proxies.
- **Reload Functionality** — Added `reload_proxies()` method for runtime proxy refresh.
- **Enhanced Logging** — Better status messages for proxy loading, retries, and failures.
- **Requirements File** — Added `requirements.txt` for easy dependency installation.

### Changed
- **Input Requirement** — `run.py` now requires complete JSON input via stdin, no defaults or environment fallbacks.
- **ProxyManager Rewrite** — Complete rewrite from hardcoded to CSV-based proxy loading.
- **Fallback Strategy** — Uses `constants/proxy.py` as fallback when CSV is missing/empty/corrupted.
- **Proxy URL Format** — Automatically builds `socks5://IP:PORT` URLs from CSV data.
- **Error Handling** — Improved exception handling with specific error types (InputError, JSONError, ProxyError, Timeout).
- **Documentation** — Updated README.md with manual proxy refresh instructions and input requirements.

### Fixed
- **Proxy Integration** — Fixed disconnect between `run_proxy_extractor.py` and proxy usage.
- **CSV Format Mismatch** — Resolved IP/port separation issue when reading CSV.
- **Windows Compatibility** — Removed emoji characters causing encoding errors on Windows.
- **Loading Performance** — Optimized CSV reading with proper encoding (UTF-8).

### Removed
- Removed premature automation files (to be redesigned properly later).

---

## [1.5.0] — 2025-11-01
### Added
- SOCKS5 proxy rotation for search and scraping modules.
- Proxy fetcher (`run_proxy_extractor.py`) to pull and validate public proxies.
- Modular `ProxyManager` with health checks and dynamic rotation.
- Adaptive output logic by mode (`research` → content only, others → summary + email).
- Full n8n compatibility with JSON I/O.

### Changed
- Replaced `WorkflowFacade.process()` runner with `run_workflow()` entrypoint.
- Updated `run.py` to read JSON input and produce JSON output (stdin/stdout model).
- Enhanced error handling and fallback for blocked proxies.
- Improved LLM prompt templates and placeholder management.

### Fixed
- DuckDuckGo blocking issue via SOCKS5 proxy rotation.
- Multiple encoding issues in scraping module.
- Input sanitization and JSON formatting errors for n8n integration.

---

## [1.4.0] — 2025-10-20
### Added
- Exception-safe workflow pipeline (`run_workflow.py`).
- Refined modular structure under `modules/` and `constants/`.

### Changed
- Unified logging and exception handling.
- Moved n8n integration from inline code to dedicated runner.

---

## [1.3.0] — 2025-10-10
### Added
- LLMModule for AI-generated summaries and proposals.
- EmailModule for personalized outreach formatting.
- Dynamic mode handling (`lead`, `research`, `general`).

---

## [1.0.0] — 2025-09-25
### Initial Release
- Basic search and scraping functionality.
- Initial workflow pipeline without proxies.
- Plain-text email generation.
