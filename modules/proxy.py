import requests
import random
import csv
import os
import shutil
import time
from datetime import datetime
from utils.helpers import search_headers, is_search_blocked
from constants.proxy import PROXIES  # Fallback proxy list
from modules.exceptions.exceptions import ProxyFailureError


class ProxyManager:
    def __init__(self, csv_path="working_proxies.csv", max_retries=3, min_proxies_threshold=10):
        """
        Initialize proxy pool from CSV file with fallback to constants.
        
        Args:
            csv_path: Path to the CSV file containing proxy list
            max_retries: Maximum number of proxy retries on failure
            min_proxies_threshold: Minimum number of proxies before warning
        """
        self.csv_path = csv_path
        self.max_retries = max_retries
        self.min_proxies_threshold = min_proxies_threshold
        self.proxy_data = self._load_proxies()
        self.proxies = [p['url'] for p in self.proxy_data]
        self.bad_proxies = set()
        self.using_csv = os.path.exists(csv_path)
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'proxies_marked_bad': 0
        }
        
    def _load_proxies(self):
        """
        Load proxies from CSV file with full row data. Falls back to constants on any error.
        
        Returns:
            List of dicts with 'url', 'ip', 'port', and 'row' (CSV row data)
        """
        proxy_data = []
        
        try:
            if not os.path.exists(self.csv_path):
                print(f"[WARNING] Proxy CSV file not found: {self.csv_path}")
                print(f"[FALLBACK] Using fallback proxies from constants ({len(PROXIES)} proxies)")
                return self._load_fallback_proxies()
            
            # Read CSV with new format (ip, port, country, city, isp, response_time_ms, status, tested_at)
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ip = row.get('ip', '').strip()
                    port = row.get('port', '').strip()
                    status = row.get('status', 'working').strip()
                    
                    # Only load working proxies
                    if ip and port and status == 'working':
                        proxy_url = f"socks5://{ip}:{port}"
                        proxy_data.append({
                            'url': proxy_url,
                            'ip': ip,
                            'port': port,
                            'country': row.get('country', 'Unknown'),
                            'city': row.get('city', 'Unknown'),
                            'isp': row.get('isp', 'Unknown'),
                            'response_time_ms': float(row.get('response_time_ms', 0)),
                            'status': status,
                            'tested_at': row.get('tested_at', ''),
                            'row': row.copy()
                        })
            
            if not proxy_data:
                print(f"[WARNING] No valid working proxies found in CSV: {self.csv_path}")
                print(f"[FALLBACK] Using fallback proxies from constants ({len(PROXIES)} proxies)")
                return self._load_fallback_proxies()
            
            # Sort by response time (fastest first)
            proxy_data.sort(key=lambda x: x['response_time_ms'])
            
            print(f"[SUCCESS] Loaded {len(proxy_data)} working proxies from {self.csv_path}")
            print(f"[INFO] Fastest proxy: {proxy_data[0]['ip']}:{proxy_data[0]['port']} ({proxy_data[0]['response_time_ms']}ms)")
            return proxy_data
            
        except Exception as e:
            print(f"[WARNING] Error loading proxies from CSV: {e}")
            print(f"[FALLBACK] Using fallback proxies from constants ({len(PROXIES)} proxies)")
            return self._load_fallback_proxies()
    
    def _load_fallback_proxies(self):
        """Load fallback proxies from constants."""
        proxy_data = []
        for proxy_url in PROXIES:
            parts = proxy_url.replace("socks5://", "").split(":")
            if len(parts) == 2:
                proxy_data.append({
                    'url': proxy_url,
                    'ip': parts[0],
                    'port': parts[1],
                    'country': 'Unknown',
                    'city': 'Unknown',
                    'isp': 'Unknown',
                    'response_time_ms': 0,
                    'status': 'working',
                    'tested_at': '',
                    'row': None
                })
        return proxy_data
    
    def _save_proxies_to_csv(self):
        """
        Save current proxy list (excluding bad proxies) back to CSV file.
        Updates status field for bad proxies.
        """
        try:
            # Filter out proxies from constants (no row data)
            proxies_with_csv_data = [p for p in self.proxy_data if p['row'] is not None]
            
            if not proxies_with_csv_data:
                print(f"[WARNING] No CSV-based proxies to save (all from fallback)")
                return False
            
            # Update status for bad proxies
            for proxy in proxies_with_csv_data:
                if proxy['url'] in self.bad_proxies:
                    proxy['status'] = 'failed'
                    if proxy['row']:
                        proxy['row']['status'] = 'failed'
            
            fieldnames = ['ip', 'port', 'country', 'city', 'isp', 'response_time_ms', 'status', 'tested_at']
            
            # Create backup
            backup_path = f"{self.csv_path}.backup"
            if os.path.exists(self.csv_path):
                try:
                    shutil.copy2(self.csv_path, backup_path)
                except Exception as e:
                    print(f"[WARNING] Could not create backup: {e}")
            
            # Atomic write
            temp_path = f"{self.csv_path}.tmp"
            with open(temp_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for proxy in proxies_with_csv_data:
                    if proxy['row']:
                        writer.writerow(proxy['row'])
            
            os.replace(temp_path, self.csv_path)
            
            working_count = len([p for p in proxies_with_csv_data if p['status'] == 'working'])
            failed_count = len([p for p in proxies_with_csv_data if p['status'] == 'failed'])
            print(f"[SUCCESS] Saved proxies to {self.csv_path} (working: {working_count}, failed: {failed_count})")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to save proxies to CSV: {e}")
            temp_path = f"{self.csv_path}.tmp"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return False
    
    def reload_proxies(self):
        """Reload proxies from CSV file and reset bad proxies."""
        print("[INFO] Reloading proxies from CSV...")
        self.bad_proxies.clear()
        self.proxy_data = self._load_proxies()
        self.proxies = [p['url'] for p in self.proxy_data]
        self.using_csv = os.path.exists(self.csv_path)
        print(f"[SUCCESS] Reloaded {len(self.proxies)} proxies")
        return len(self.proxies)
    
    def get_proxy(self, prefer_fast=True):
        """
        Get a proxy from the pool (excluding bad proxies).
        
        Args:
            prefer_fast: If True, prefer faster proxies. If False, random selection.
            
        Returns:
            Proxy URL string or None if no proxies available
        """
        if not self.proxies:
            print("[WARNING] No proxies available")
            return None
        
        # Filter out bad proxies
        available_proxies = [p for p in self.proxy_data if p['url'] not in self.bad_proxies]
        
        if not available_proxies:
            print("[WARNING] All proxies marked as bad, resetting bad proxy list")
            self.bad_proxies.clear()
            available_proxies = self.proxy_data.copy()
        
        # Check if we're running low on proxies
        if len(available_proxies) < self.min_proxies_threshold:
            print(f"[WARNING] Running low on proxies! Only {len(available_proxies)} available (threshold: {self.min_proxies_threshold})")
            print(f"[HINT] Consider running proxy extraction script to refresh proxy list")
        
        if prefer_fast:
            # Prefer faster proxies (80% chance to pick from top 30%)
            if random.random() < 0.8:
                top_30_percent = max(1, len(available_proxies) // 3)
                proxy_entry = random.choice(available_proxies[:top_30_percent])
            else:
                proxy_entry = random.choice(available_proxies)
        else:
            proxy_entry = random.choice(available_proxies)
        
        return proxy_entry['url']
    
    def mark_proxy_bad(self, proxy):
        """
        Mark a proxy as bad and persist to CSV.
        
        Args:
            proxy: Proxy URL to mark as bad (format: socks5://IP:PORT)
        """
        if not proxy or proxy in self.bad_proxies:
            return
        
        # Find the proxy entry
        proxy_entry = None
        for p in self.proxy_data:
            if p['url'] == proxy:
                proxy_entry = p
                break
        
        self.bad_proxies.add(proxy)
        self.stats['proxies_marked_bad'] += 1
        
        if proxy_entry:
            proxy_entry['status'] = 'failed'
            if proxy_entry['row']:
                proxy_entry['row']['status'] = 'failed'
        
        print(f"[DELIST] Marked proxy as bad: {proxy} ({len(self.bad_proxies)} bad proxies, {self.get_available_proxy_count()} remaining)")
        
        # Persist to CSV if from CSV source
        if proxy_entry and proxy_entry['row'] is not None:
            self._save_proxies_to_csv()
    
    def get_available_proxy_count(self):
        """Get the number of available (good) proxies."""
        return len([p for p in self.proxies if p not in self.bad_proxies])
    
    def get_proxy_count(self):
        """Get the total number of proxies."""
        return len(self.proxies)
    
    def get_stats(self):
        """Get usage statistics."""
        available = self.get_available_proxy_count()
        total = self.get_proxy_count()
        success_rate = (self.stats['successful_requests'] / self.stats['total_requests'] * 100) if self.stats['total_requests'] > 0 else 0
        
        return {
            **self.stats,
            'available_proxies': available,
            'total_proxies': total,
            'bad_proxies': len(self.bad_proxies),
            'success_rate': round(success_rate, 2)
        }
    
    def print_stats(self):
        """Print usage statistics."""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("📊 Proxy Manager Statistics")
        print("=" * 60)
        print(f"Total Proxies: {stats['total_proxies']}")
        print(f"Available Proxies: {stats['available_proxies']}")
        print(f"Bad Proxies: {stats['bad_proxies']}")
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Successful Requests: {stats['successful_requests']}")
        print(f"Failed Requests: {stats['failed_requests']}")
        print(f"Success Rate: {stats['success_rate']}%")
        print("=" * 60 + "\n")

    def fetch(self, url, prefer_fast=True):
        """
        Fetch URL using a random proxy with automatic retry on failure.
        
        Args:
            url: URL to fetch
            prefer_fast: Prefer faster proxies
            
        Returns:
            Tuple of (response_text, response_object)
            
        Raises:
            ProxyFailureError: When all proxy attempts fail
        """
        self.stats['total_requests'] += 1
        last_error = None
        request_start_time = time.time()
        
        for attempt in range(self.max_retries):
            proxy = self.get_proxy(prefer_fast=prefer_fast)
            
            if not proxy:
                print("[WARNING] No proxy available for request")
                self.stats['failed_requests'] += 1
                raise ProxyFailureError(
                    url,
                    f"No proxies available. Total: {self.get_proxy_count()}, Available: {self.get_available_proxy_count()}"
                )
            
            # Log proxy attempt with timing
            attempt_start = time.time()
            proxy_ip = proxy.split('//')[1].split(':')[0] if '//' in proxy else proxy
            if "duckduckgo.com" in url.lower():
                print(f"[PROXY] Attempt {attempt + 1}/{self.max_retries}: Trying proxy {proxy_ip}...")
            
            headers = search_headers()
            
            try:
                r = requests.get(
                    url,
                    headers=headers,
                    proxies={"http": proxy, "https": proxy},
                    timeout=36,
                    verify=False
                )
                
                attempt_time = time.time() - attempt_start
                if "duckduckgo.com" in url.lower():
                    print(f"[PROXY] Proxy {proxy_ip} responded in {attempt_time:.2f}s (HTTP {r.status_code})")
                
                # Check if response is successful
                if r.status_code != 200:
                    print(f"[ERROR] HTTP {r.status_code} with {proxy_ip} after {attempt_time:.2f}s (attempt {attempt + 1}/{self.max_retries})")
                    self.mark_proxy_bad(proxy)
                    last_error = Exception(f"HTTP {r.status_code}")
                    continue
                
                # Check for blocking indicators (especially for DuckDuckGo)
                # This helps identify proxies that connect but are blocked
                if "duckduckgo.com" in url.lower() and is_search_blocked(r.text):
                    print(f"[ERROR] Proxy {proxy_ip} blocked by DuckDuckGo after {attempt_time:.2f}s (attempt {attempt + 1}/{self.max_retries})")
                    self.mark_proxy_bad(proxy)
                    last_error = Exception("DuckDuckGo blocked this proxy")
                    continue
                
                # Success!
                self.stats['successful_requests'] += 1
                total_time = time.time() - request_start_time
                if attempt > 0:
                    print(f"[SUCCESS] Request succeeded on attempt {attempt + 1} with proxy {proxy_ip} (total time: {total_time:.2f}s)")
                elif "duckduckgo.com" in url.lower():
                    print(f"[PROXY] Successfully fetched with {proxy_ip} in {total_time:.2f}s")
                return r.text, r
                
            except (requests.exceptions.ProxyError, requests.exceptions.Timeout, 
                    requests.exceptions.ConnectionError) as e:
                attempt_time = time.time() - attempt_start
                if "duckduckgo.com" in url.lower():
                    print(f"[ERROR] {type(e).__name__} with {proxy_ip} after {attempt_time:.2f}s (attempt {attempt + 1}/{self.max_retries})")
                else:
                    print(f"[ERROR] {type(e).__name__} with {proxy} (attempt {attempt + 1}/{self.max_retries})")
                self.mark_proxy_bad(proxy)
                last_error = e
                
            except Exception as e:
                attempt_time = time.time() - attempt_start
                if "duckduckgo.com" in url.lower():
                    print(f"[ERROR] Unexpected error with {proxy_ip} after {attempt_time:.2f}s (attempt {attempt + 1}/{self.max_retries}): {e}")
                else:
                    print(f"[ERROR] Unexpected error with {proxy} (attempt {attempt + 1}/{self.max_retries}): {e}")
                self.mark_proxy_bad(proxy)
                last_error = e
        
        # All retries exhausted
        self.stats['failed_requests'] += 1
        print(f"[FAILED] All {self.max_retries} proxy attempts failed for {url}")
        error_msg = f"All {self.max_retries} proxy attempts failed. Available: {self.get_available_proxy_count()}/{self.get_proxy_count()}"
        if last_error:
            error_msg += f". Last error: {str(last_error)}"
        
        raise ProxyFailureError(url, error_msg)


# Global proxy manager instance
proxy = ProxyManager(csv_path="working_proxies.csv", max_retries=3, min_proxies_threshold=10)
