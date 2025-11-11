import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.helpers import is_search_blocked, extract_real_url, search_headers, is_navigational_content,contains_keywords

class Scraper:
    def __init__(self):
        """Initialize scraper with connection pooling for better performance."""
        # Connection pooling: reuse HTTP connections
        self.session = requests.Session()
        # Set default headers that will be reused
        self.session.headers.update(search_headers())
    
    def extract_links(self, html: str, max_links: int) -> List[Dict]:
        out = []
        if not html or is_search_blocked(html):
            return out
        soup = BeautifulSoup(html, "lxml")
        results = soup.select("a.result__a") or soup.select(".result__body a.result__a")
        for a in results:
            href = a.get("href")
            if not href:
                continue
            real = extract_real_url(href)
            title = a.get_text(strip=True)
            snippet_el = a.find_next("a")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            out.append({"url": real, "title": title, "snippet": snippet})
            if len(out) >= max_links:
                break
        return out

    def fetch_page_content(self, url: str, timeout: int = 5, retry_timeout: int = 3) -> str:
        """
        Fetch page content with connection pooling and adaptive timeouts.
        Uses the shared session for connection pooling.
        
        Args:
            url: URL to fetch
            timeout: Initial timeout in seconds (default: 5)
            retry_timeout: Retry timeout in seconds (default: 3)
        """
        return self._fetch_with_session(self.session, url, timeout, retry_timeout)
    
    def extract_relevant_content(self, html: str, max_chars: int = 2000) -> str:
        """
        Extract relevant content with selective parsing and early termination.
        Targets main content areas first, then falls back to all paragraphs.
        Stops parsing once we have enough content (~2000 chars).
        
        Args:
            html: HTML content to parse
            max_chars: Maximum characters to extract (default: 2000)
        """
        if not html:
            return ""
    
        soup = BeautifulSoup(html, "lxml")
        useful_content = []
        seen_texts = set()  # Use set for O(1) duplicate checking
        total_length = 0
        
        # Selective parsing: Try main content areas first (faster, more relevant)
        # Priority order: main > article > .content/.main-content > all paragraphs
        content_selectors = [
            "main p, main div",
            "article p, article div", 
            ".content p, .content div, .main-content p, .main-content div",
            "p, div"  # Fallback to all paragraphs/divs
        ]
        
        for selector in content_selectors:
            if total_length >= max_chars:
                break
                
            paragraphs = soup.select(selector)
            
            # Early termination: stop once we have enough content
            for p in paragraphs:
                text = p.get_text(strip=True)
                
                # Skip empty or very short text early
                if not text or len(text) < 10:
                    continue
                
                # Optimize keyword checking: lowercase once, then check
                text_lower = text.lower()
                
                # Skip if navigational or doesn't contain keywords
                # Pass lowercased text to avoid re-lowercasing in contains_keywords
                if is_navigational_content(text) or not contains_keywords(text_lower):
                    continue
                
                # Skip if we already have this text (O(1) lookup with set)
                if text in seen_texts:
                    continue
                
                # Add to both list and set
                useful_content.append(text)
                seen_texts.add(text)
                total_length += len(text)
                
                # Stop early if we have enough content
                if total_length >= max_chars:
                    break
            
            # If we got enough content from a priority selector, don't try fallback
            if total_length >= max_chars:
                break

        # Join and limit to max_chars (in case last addition went over)
        result = " ".join(useful_content)
        return result[:max_chars] if len(result) > max_chars else result

    def _scrape_single_link(self, link: Dict) -> Dict:
        """
        Scrape a single link (thread-safe, creates its own session).
        Used for parallel scraping.
        
        Args:
            link: Link dictionary with url, title, snippet
            
        Returns:
            Dictionary with scraped content or None if failed
        """
        # Create a new session for this thread (requests.Session is not thread-safe)
        thread_session = requests.Session()
        thread_session.headers.update(search_headers())
        
        try:
            # Fetch page content
            html = self._fetch_with_session(thread_session, link["url"])
            if not html:
                return None
            
            # Extract relevant content
            content = self.extract_relevant_content(html)
            if content:
                return {
                    "url": link["url"],
                    "title": link["title"],
                    "snippet": link["snippet"],
                    "content": content
                }
        except Exception:
            pass
        finally:
            # Close the session
            thread_session.close()
        
        return None
    
    def _fetch_with_session(self, session: requests.Session, url: str, timeout: int = 5, retry_timeout: int = 3) -> str:
        """
        Fetch page content using a provided session (for thread-safety).
        
        Args:
            session: requests.Session to use
            url: URL to fetch
            timeout: Initial timeout in seconds (default: 5)
            retry_timeout: Retry timeout in seconds (default: 3)
        """
        # Try with initial timeout
        try:
            r = session.get(url, timeout=timeout, stream=True)
            
            # Check Content-Length header to skip very large pages
            content_length = r.headers.get('content-length')
            if content_length and int(content_length) > 2_000_000:  # Skip pages > 2MB
                r.close()
                return ""
            
            if r.status_code == 200:
                return r.text
        except requests.exceptions.Timeout:
            # Retry with shorter timeout
            try:
                r = session.get(url, timeout=retry_timeout, stream=True)
                content_length = r.headers.get('content-length')
                if content_length and int(content_length) > 2_000_000:
                    r.close()
                    return ""
                if r.status_code == 200:
                    return r.text
            except Exception:
                pass
        except Exception:
            pass
        return ""
    
    def scrape_links_content(self, links: List[Dict], max_workers: int = 10) -> List[Dict]:
        """
        Scrape multiple links in parallel using ThreadPoolExecutor.
        
        Args:
            links: List of link dictionaries to scrape
            max_workers: Number of parallel workers (default: 10, increased for better performance)
            
        Returns:
            List of dictionaries with scraped content
        """
        if not links:
            return []
        
        # Limit max_workers to number of links
        max_workers = min(max_workers, len(links))
        
        out = []
        
        # Use ThreadPoolExecutor for parallel scraping
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scraping tasks
            future_to_link = {
                executor.submit(self._scrape_single_link, link): link
                for link in links
            }
            
            # Process completed futures
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    result = future.result()
                    if result:
                        out.append(result)
                except Exception:
                    # Handle any errors silently
                    pass
        
        return out
    
    def extract_and_scrape(self, search_html: str, max_links: int) -> List[Dict]:
        links = self.extract_links(search_html, max_links)
        return self.scrape_links_content(links)
