import requests
import csv
import time
import random
import threading
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from utils.helpers import search_headers, is_search_blocked
from concurrent.futures import ThreadPoolExecutor, as_completed, CancelledError
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DUCK_SEARCH_BASE = "https://duckduckgo.com/html/"


class DuckDuckGoProxyTester:
    def __init__(self, timeout=15, test_queries=None):
        """
        Initialize the proxy tester.
        
        Args:
            timeout: Request timeout in seconds
            test_queries: List of test queries to use for testing. If None, uses defaults.
        """
        self.timeout = timeout
        self.test_queries = test_queries or [
            "python programming",
            "artificial intelligence",
            "technology news"
        ]
        self.working_proxies = []
        self.failed_proxies = []
        self.lock = threading.Lock()  # Thread lock for shared data structures
        self.tested_count = 0
        self.start_time = None
        
    # Public SOCKS5 sources
    PROXY_SOURCES = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    ]
    
    def fetch_proxies_from_sources(self) -> List[str]:
        """Fetch proxies from multiple sources"""
        all_proxies = set()
        
        print("🔍 Fetching proxies from public sources...\n")
        
        for url in self.PROXY_SOURCES:
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    proxies = []
                    for line in response.text.strip().split('\n'):
                        line = line.strip()
                        # Validate proxy format: IP:PORT
                        if ':' in line and line.count(':') == 1:
                            parts = line.split(':')
                            if len(parts) == 2 and parts[1].isdigit():
                                all_proxies.add(line)
                                proxies.append(line)
                    print(f"✅ Fetched {len(proxies)} from {url[:60]}...")
            except Exception as e:
                print(f"❌ Failed {url[:60]}: {str(e)[:50]}")
        
        print(f"\n📊 Total unique proxies collected: {len(all_proxies)}\n")
        return list(all_proxies)
    
    def test_proxy_with_duckduckgo(self, proxy: str, test_query: str = None) -> Optional[Dict]:
        """
        Test a proxy against DuckDuckGo with a real search query.
        This matches the actual production usage.
        
        Args:
            proxy: Proxy in format "IP:PORT"
            test_query: Query to test with. If None, uses a random query from test_queries.
            
        Returns:
            Dict with proxy info if successful, None if failed
        """
        if test_query is None:
            test_query = random.choice(self.test_queries)
        
        try:
            ip, port = proxy.split(':')
        except ValueError:
            return None
        
        proxy_url = f"socks5://{proxy}"
        
        # Format search URL exactly like production
        query = quote_plus(test_query)
        search_url = f"{DUCK_SEARCH_BASE}?q={query}&s=0"
        
        try:
            start_time = time.time()
            
            # Use the same headers as production
            headers = search_headers()
            
            # Make request using requests library (same as production)
            response = requests.get(
                search_url,
                headers=headers,
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=self.timeout,
                verify=False  # Same as production
            )
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # Check if request was successful
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # Check for blocking indicators (same as production)
            if is_search_blocked(html):
                return None
            
            # Verify we got actual search results
            try:
                soup = BeautifulSoup(html, "lxml")
                results = soup.select("a.result__a") or soup.select(".result__body a.result__a")
                
                # Must have at least 3 search results to be considered valid
                if len(results) < 3:
                    return None
            except Exception:
                # Parsing error - likely invalid HTML
                return None
            
            # Test passed! Get proxy location info (optional, don't fail if this fails)
            country = 'Unknown'
            city = 'Unknown'
            isp = 'Unknown'
            
            try:
                # Try to get location info from IP-API (quick timeout, don't block)
                ip_info_response = requests.get(
                    f"http://ip-api.com/json/{ip}",
                    timeout=3,
                    proxies={"http": proxy_url, "https": proxy_url}
                )
                if ip_info_response.status_code == 200:
                    ip_data = ip_info_response.json()
                    country = ip_data.get('country', 'Unknown')
                    city = ip_data.get('city', 'Unknown')
                    isp = ip_data.get('isp', 'Unknown')
            except:
                # Location info is optional, continue without it
                pass
            
            return {
                'ip': ip,
                'port': port,
                'country': country,
                'city': city,
                'isp': isp,
                'response_time_ms': response_time,
                'status': 'working',
                'tested_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'test_query': test_query,
                'results_count': len(results)
            }
            
        except (requests.exceptions.ProxyError, 
                requests.exceptions.Timeout, 
                requests.exceptions.ConnectionError,
                requests.exceptions.RequestException):
            # Proxy connection failed
            return None
        except Exception:
            # Other errors (parsing, etc.)
            return None
    
    def test_proxy_multiple_queries(self, proxy: str, num_tests: int = 2) -> Optional[Dict]:
        """
        Test a proxy with multiple queries to ensure it's reliable.
        
        Args:
            proxy: Proxy in format "IP:PORT"
            num_tests: Number of test queries to run
            
        Returns:
            Dict with proxy info if all tests pass, None if any test fails
        """
        results = []
        
        # Test with different queries
        test_queries = random.sample(self.test_queries, min(num_tests, len(self.test_queries)))
        
        for query in test_queries:
            result = self.test_proxy_with_duckduckgo(proxy, query)
            if result is None:
                # One test failed, proxy is not reliable
                return None
            results.append(result)
            # Small delay between tests to avoid rate limiting (reduced for parallel execution)
            # Since we're testing in parallel, we can reduce this delay
            time.sleep(0.1)
        
        # All tests passed - use the first result (they should be similar)
        # Average response time across tests
        avg_response_time = sum(r['response_time_ms'] for r in results) / len(results)
        result = results[0]
        result['response_time_ms'] = round(avg_response_time, 2)
        result['tests_passed'] = len(results)
        
        return result
    
    def test_single_proxy(self, proxy: str, test_per_proxy: int) -> Optional[Dict]:
        """
        Test a single proxy and update shared state (thread-safe).
        
        Args:
            proxy: Proxy to test
            test_per_proxy: Number of tests to run per proxy
            
        Returns:
            Dict with proxy info if successful, None if failed
        """
        # Test the proxy
        result = self.test_proxy_multiple_queries(proxy, test_per_proxy)
        
        # Update shared state (thread-safe)
        with self.lock:
            self.tested_count += 1
            tested = self.tested_count
            total_proxies = getattr(self, 'total_proxies', 0)
            
            if result:
                self.working_proxies.append(result)
                working_count = len(self.working_proxies)
                
                # Only print successful proxies (they're important)
                status = f"✅ {proxy} | {result['country']} | {result['response_time_ms']}ms | {result['results_count']} results"
                print(status)
                
                # Progress update every 10 tested proxies
                if tested % 10 == 0:
                    elapsed = time.time() - self.start_time if self.start_time else 0
                    rate = tested / elapsed if elapsed > 0 else 0
                    remaining = total_proxies - tested
                    eta_seconds = remaining / rate if rate > 0 and remaining > 0 else 0
                    eta_minutes = eta_seconds / 60
                    
                    print(f"\n📊 Progress: {tested}/{total_proxies} tested | "
                          f"{working_count} working | {len(self.failed_proxies)} failed | "
                          f"Rate: {rate:.1f}/sec", end="")
                    if eta_seconds > 0:
                        print(f" | ETA: {eta_minutes:.1f}min", end="")
                    print("\n")
                
                return result
            else:
                self.failed_proxies.append(proxy)
                # Don't print failures to reduce noise - only show progress updates
                return None
    
    def test_proxies_parallel(self, proxies: List[str], test_per_proxy: int = 2, max_workers: int = 30):
        """
        Test proxies in parallel using ThreadPoolExecutor.
        Tests ALL proxies and collects ALL working ones.
        
        Args:
            proxies: List of proxies to test
            test_per_proxy: Number of tests to run per proxy
            max_workers: Number of concurrent threads (default: 30)
        """
        self.total_proxies = len(proxies)
        self.start_time = time.time()
        
        print(f"🧪 Testing {len(proxies)} proxies against DuckDuckGo...")
        print(f"📋 Using {test_per_proxy} test queries per proxy")
        print(f"🔀 Parallel workers: {max_workers}")
        print(f"🎯 Collecting ALL working proxies (no limit)")
        print(f"⏱️  Estimated time: ~{len(proxies) / (max_workers * 2):.1f} minutes (approximate)\n")
        print("Testing in progress... (only showing successful proxies)\n")
        
        # Shuffle proxies for better distribution
        random.shuffle(proxies)
        
        # Use ThreadPoolExecutor for parallel testing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all proxy tests
            future_to_proxy = {
                executor.submit(self.test_single_proxy, proxy, test_per_proxy): proxy
                for proxy in proxies
            }
            
            # Process completed futures - test ALL proxies
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    future.result()  # This will raise any exceptions that occurred
                except Exception as e:
                    # Handle any unexpected errors
                    with self.lock:
                        self.tested_count += 1
                        self.failed_proxies.append(proxy)
        
        elapsed = time.time() - self.start_time
        elapsed_minutes = elapsed / 60
        
        print(f"\n✅ Testing complete! (took {elapsed_minutes:.1f} minutes)")
        print(f"   Working: {len(self.working_proxies)}")
        print(f"   Failed: {len(self.failed_proxies)}")
        print(f"   Success rate: {len(self.working_proxies)/self.tested_count*100:.1f}%")
        print(f"   Average rate: {self.tested_count/elapsed:.1f} proxies/second")
    
    def save_to_csv(self, filename='working_proxies.csv'):
        """Save working proxies to CSV"""
        if not self.working_proxies:
            print("\n❌ No working proxies found!")
            print("💡 This could mean:")
            print("   - All proxies are blocked by DuckDuckGo")
            print("   - Network connectivity issues")
            print("   - Proxy sources are outdated")
            return
        
        # Sort by response time (fastest first)
        self.working_proxies.sort(key=lambda x: x['response_time_ms'])
        
        # Keep only top proxies (remove duplicates and keep fastest)
        seen = set()
        unique_proxies = []
        for proxy in self.working_proxies:
            proxy_key = f"{proxy['ip']}:{proxy['port']}"
            if proxy_key not in seen:
                seen.add(proxy_key)
                unique_proxies.append(proxy)
        
        # Remove test-specific fields before saving
        for proxy in unique_proxies:
            proxy.pop('test_query', None)
            proxy.pop('results_count', None)
            proxy.pop('tests_passed', None)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ip', 'port', 'country', 'city', 'isp', 'response_time_ms', 'status', 'tested_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_proxies)
        
        print(f"\n💾 Saved {len(unique_proxies)} working proxies to '{filename}'")
        if unique_proxies:
            fastest = unique_proxies[0]
            slowest = unique_proxies[-1]
            print(f"⚡ Fastest: {fastest['ip']}:{fastest['port']} ({fastest['response_time_ms']}ms) - {fastest['country']}")
            print(f"🐌 Slowest: {slowest['ip']}:{slowest['port']} ({slowest['response_time_ms']}ms) - {slowest['country']}")
            print(f"📊 Average response time: {sum(p['response_time_ms'] for p in unique_proxies)/len(unique_proxies):.1f}ms")
    
    def run(self, test_per_proxy=2, max_workers=30):
        """
        Main execution - tests ALL proxies and collects ALL working ones.
        
        Args:
            test_per_proxy: Number of tests to run per proxy
            max_workers: Number of concurrent threads (default: 30, adjust based on your system)
        """
        print("=" * 70)
        print("🚀 DuckDuckGo Proxy Tester (Parallel)")
        print("   Tests proxies against actual DuckDuckGo search (production-like)")
        print("   Collects ALL working proxies (no limit)")
        print("=" * 70 + "\n")
        
        # Fetch proxies
        proxies = self.fetch_proxies_from_sources()
        
        if not proxies:
            print("❌ No proxies found from sources!")
            return
        
        # Test proxies in parallel - test ALL of them
        self.test_proxies_parallel(
            proxies, 
            test_per_proxy=test_per_proxy,
            max_workers=max_workers
        )
        
        # Save results
        self.save_to_csv()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 Final Statistics")
        print("=" * 70)
        print(f"Total proxies tested: {self.tested_count}")
        print(f"Working proxies: {len(self.working_proxies)}")
        print(f"Failed proxies: {len(self.failed_proxies)}")
        if self.tested_count > 0:
            print(f"Success rate: {len(self.working_proxies)/self.tested_count*100:.1f}%")
        print("=" * 70)


if __name__ == "__main__":
    tester = DuckDuckGoProxyTester(timeout=15, test_queries=[
        "python programming",
        "artificial intelligence", 
        "technology news",
        "web development",
        "data science"
    ])
    
    # Test ALL proxies, run 2 tests per proxy, use 30 parallel workers
    # Adjust max_workers based on your system (20-50 is a good range)
    tester.run(test_per_proxy=2, max_workers=30)
