import time
import random
import threading
from playwright.sync_api import sync_playwright
from fake_useragent import UserAgent
import requests
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from urllib.parse import urlparse, quote_plus
import re
import subprocess
import platform
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'seo_traffic_booster_secret')
socketio = SocketIO(app, async_mode='eventlet') 

class SEOTrafficBooster:
    def __init__(self):
        self.ua = UserAgent()
        self.is_running = False
        self.current_status = "Ready"
        self.current_cycle = 0
        self.total_cycles = 0
        self.current_proxy = None
        self.proxy_ping_times = {}
        self.current_target_website = None
        
    def update_status(self, message):
        """Update status dan kirim ke UI"""
        self.current_status = message
        timestamp = time.strftime("%H:%M:%S")
        socketio.emit('status_update', {
            'message': f"[{timestamp}] {message}",
            'cycle': self.current_cycle,
            'total_cycles': self.total_cycles,
            'current_proxy': self.current_proxy
        })
        print(f"[{timestamp}] {message}")
    
    def ping_proxy(self, proxy_host):
        """Mengukur ping ke proxy server"""
        try:
            if '@' in proxy_host:
                proxy_host = proxy_host.split('@')[1]
            
            host = proxy_host.split(':')[0]
            
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '2', host]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                if 'time=' in result.stdout:
                    time_line = [line for line in result.stdout.split('\n') if 'time=' in line][0]
                    ping_time = re.search(r'time=([\d.]+)\s*ms', time_line)
                    if ping_time:
                        return float(ping_time.group(1))
            return None
        except:
            return None
    
    def get_proxy_delay(self):
        """Dapatkan delay berdasarkan ping proxy"""
        if self.current_proxy and self.current_proxy in self.proxy_ping_times:
            ping_time = self.proxy_ping_times[self.current_proxy]
            if ping_time < 100: return 2
            elif ping_time < 300: return 4
            elif ping_time < 500: return 6
            else: return 8
        return 3
        
    def setup_browser(self, proxy_list):
        """Setup Playwright browser dengan konfigurasi stealth"""
        try:
            playwright = sync_playwright().start()
            
            # Proxy configuration
            proxy_arg = None
            if proxy_list:
                proxy = random.choice(proxy_list)
                self.current_proxy = proxy
                
                ping_time = self.ping_proxy(proxy)
                if ping_time:
                    self.update_status(f"Using proxy: {proxy} (ping: {ping_time:.0f}ms)")
                    self.proxy_ping_times[proxy] = ping_time
                else:
                    self.update_status(f"Using proxy: {proxy} (ping: unknown)")
                
                # Format proxy untuk Playwright
                if '@' in proxy:
                    proxy_arg = {'server': f'http://{proxy}'}
                else:
                    proxy_arg = {'server': f'http://{proxy}'}
            else:
                self.current_proxy = None
                self.update_status("Running without proxy")

            # Browser launch options untuk Render.com
            launch_options = {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding'
                ]
            }

            if proxy_arg:
                launch_options['proxy'] = proxy_arg

            # Untuk Render.com, gunakan chromium
            browser = playwright.chromium.launch(**launch_options)

            # Context options
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': self.ua.random,
                'ignore_https_errors': True,
            }

            context = browser.new_context(**context_options)

            # Add stealth scripts
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                window.chrome = {
                    runtime: {},
                };
            """)

            page = context.new_page()
            
            # Set timeouts
            page.set_default_timeout(60000)
            page.set_default_navigation_timeout(60000)

            return playwright, browser, context, page

        except Exception as e:
            self.update_status(f"Error setting up browser: {str(e)}")
            if proxy_list:
                self.update_status("Trying without proxy...")
                return self.setup_browser([])
            return None, None, None, None
    
    def test_proxy(self, proxy):
        """Test jika proxy berfungsi"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
            
            ping_time = self.ping_proxy(proxy)
            timeout = 10 + (ping_time / 1000 if ping_time else 5)
            
            response = requests.get(test_url, proxies=proxies, timeout=timeout)
            return response.status_code == 200
        except:
            return False
    
    def get_working_proxies(self, proxy_list):
        """Filter proxy yang berfungsi"""
        working_proxies = []
        self.update_status(f"Testing {len(proxy_list)} proxies...")
        
        for proxy in proxy_list:
            if not self.is_running:
                break
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
                self.update_status(f"✓ Proxy {proxy} works")
            else:
                self.update_status(f"✗ Proxy {proxy} failed")
        
        self.update_status(f"Found {len(working_proxies)} working proxies")
        return working_proxies
    
    def generate_keywords_from_url(self, url):
        """Generate keyword SEO otomatis dari URL"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            
            if 'blogspot.com' in domain:
                blog_name = domain.replace('.blogspot.com', '')
                keywords = [
                    blog_name, f"{blog_name} blog", f"{blog_name} articles",
                    f"{blog_name} posts", "blogspot", "blogger", "blog"
                ]
            else:
                domain_keywords = domain.replace('.com', '').replace('.org', '').replace('.net', '').split('.')
                keywords = []
                for kw in domain_keywords:
                    if kw and len(kw) > 2:
                        keywords.extend([kw, f"{kw} blog", f"{kw} website", f"{kw} online"])
            
            final_keywords = []
            for kw in keywords[:6]:
                final_keywords.extend([
                    kw, f"site:{domain} {kw}", f"{kw} latest", 
                    f"{kw} update", f"what is {kw}", f"about {kw}"
                ])
            
            return list(set(final_keywords))[:15]
        
        except Exception as e:
            self.update_status(f"Error generating keywords: {str(e)}")
            return ["blog", "articles", "posts", "website", "online content"]
    
    def build_google_search_url(self, keyword):
        """Bangun URL pencarian Google"""
        encoded_keyword = quote_plus(keyword)
        return f"https://www.google.com/search?q={encoded_keyword}"
    
    def extract_domain_patterns(self, url):
        """Ekstrak pola domain untuk pencarian"""
        parsed = urlparse(url)
        full_domain = parsed.netloc
        clean_domain = full_domain.replace('www.', '')
        
        patterns = [clean_domain, full_domain]
        
        if 'blogspot.com' in clean_domain:
            blog_name = clean_domain.replace('.blogspot.com', '')
            patterns.extend([
                blog_name,
                f"{blog_name}.blogspot.com",
                f"www.{blog_name}.blogspot.com",
                f"https://{blog_name}.blogspot.com",
                f"https://{blog_name}.blogspot.com/",
                f"http://{blog_name}.blogspot.com"
            ])
        
        if parsed.path and parsed.path != '/':
            path_clean = parsed.path.strip('/')
            patterns.extend([f"{clean_domain}/{path_clean}", f"{full_domain}/{path_clean}"])
        
        return list(set(patterns))
    
    def handle_google_sorry_page(self, page):
        """Deteksi dan handle halaman Google Sorry/CAPTCHA"""
        try:
            current_url = page.url
            if "google.com/sorry" in current_url or "blocked" in current_url.lower():
                self.update_status("⚠️ Detected Google Sorry/CAPTCHA page")
                
                # Multiple bypass strategies
                if self.bypass_with_direct_access(page):
                    return True
                if self.bypass_with_user_agent_rotation(page):
                    return True
                
                self.update_status("❌ Failed to bypass Sorry page")
                return False
            return True
        except Exception as e:
            self.update_status(f"Error handling sorry page: {str(e)}")
            return False

    def bypass_with_direct_access(self, page):
        """Bypass dengan akses langsung"""
        try:
            if hasattr(self, 'current_target_website'):
                page.goto(self.current_target_website, wait_until='networkidle')
                time.sleep(5)
                return "sorry" not in page.url.lower()
        except:
            pass
        return False

    def bypass_with_user_agent_rotation(self, page):
        """Rotate User Agent"""
        try:
            new_ua = self.ua.random
            page.set_extra_http_headers({'User-Agent': new_ua})
            page.reload(wait_until='networkidle')
            time.sleep(3)
            return "sorry" not in page.url.lower()
        except:
            return False
    
    def find_target_links_advanced(self, page, target_website):
        """Mencari link target dengan Playwright"""
        domain_patterns = self.extract_domain_patterns(target_website)
        found_links = []
        
        self.update_status(f"Searching with {len(domain_patterns)} domain patterns...")
        
        # CSS Selectors untuk hasil Google
        selectors = [
            "div.g a[href*='blogspot']",
            "a[href*='blogspot.com']",
            "h3 a",
            ".yuRUbf a", 
            ".rc .r a",
            "a[data-ved]"
        ]
        
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                for elem in elements:
                    try:
                        href = elem.get_attribute('href')
                        if href:
                            for pattern in domain_patterns:
                                if pattern.lower() in href.lower():
                                    link_text = elem.text_content()[:30] if elem.text_content() else "no-text"
                                    self.update_status(f"✅ Found: {link_text}...")
                                    found_links.append(elem)
                                    break
                    except:
                        continue
                if found_links:
                    break
            except:
                continue
        
        # Fallback: cari semua link
        if not found_links:
            self.update_status("Searching all links on page...")
            all_links = page.query_selector_all("a")
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href and any(pattern in href.lower() for pattern in domain_patterns):
                        found_links.append(link)
                except:
                    continue
        
        # Remove duplicates
        unique_links = []
        seen_hrefs = set()
        for link in found_links:
            try:
                href = link.get_attribute('href')
                if href and href not in seen_hrefs:
                    seen_hrefs.add(href)
                    unique_links.append(link)
            except:
                continue
        
        return unique_links
    
    def smart_click(self, page, element):
        """Klik element dengan Playwright"""
        try:
            # Scroll ke element
            element.scroll_into_view_if_needed()
            time.sleep(1)
            
            # Klik dengan Playwright
            element.click()
            return True
        except:
            try:
                # Klik dengan JavaScript
                page.evaluate("(element) => element.click()", element)
                return True
            except:
                return False

    def natural_scroll_behavior(self, page):
        """Scroll behavior yang natural"""
        try:
            scroll_actions = [
                {"y": 300, "delay": 1},
                {"y": 800, "delay": 2},
                {"y": 1200, "delay": 1},
                {"y": 500, "delay": 1},
                {"y": 1500, "delay": 3}
            ]
            
            for action in scroll_actions:
                page.evaluate(f"window.scrollTo(0, {action['y']})")
                time.sleep(action['delay'] + random.uniform(0.5, 1.5))
        except Exception as e:
            self.update_status(f"Scroll error: {str(e)}")
    
    def click_and_verify_target(self, page, element, target_website):
        """Klik link dan verifikasi"""
        try:
            link_href = element.get_attribute('href')
            self.update_status(f"Selected: {link_href[:100]}...")
            
            if self.smart_click(page, element):
                self.update_status("Successfully clicked target website")
                
                proxy_delay = self.get_proxy_delay()
                time.sleep(random.uniform(6 + proxy_delay, 10 + proxy_delay))
                
                # Verifikasi URL target
                current_url = page.url
                domain_patterns = self.extract_domain_patterns(target_website)
                is_correct_site = any(pattern in current_url for pattern in domain_patterns)
                
                if is_correct_site:
                    self.update_status("✅ Successfully reached target website")
                    
                    # 🔥 ACTIVITAS TAMBAHAN: Klik iklan Google Ads
                    self.click_google_ads(page, target_website)
                    
                    # Kembali ke website target setelah klik ads
                    page.goto(target_website, wait_until='networkidle')
                    time.sleep(3)
                    
                    # 🔥 ACTIVITAS TAMBAHAN: Klik postingan acak dan baca
                    self.read_random_post(page, target_website)
                    
                    self.slow_scroll(page)
                    self.click_random_internal_link(page, target_website)
                    return True
                else:
                    self.update_status("❌ Redirected to different site")
                    return self.direct_website_access(page, target_website)
            else:
                self.update_status("❌ Failed to click link")
                return self.direct_website_access(page, target_website)
                
        except Exception as e:
            self.update_status(f"❌ Error clicking target: {str(e)}")
            return self.direct_website_access(page, target_website)
    
    def click_google_ads(self, page, target_website):
        """Klik iklan Google Ads jika ada"""
        try:
            self.update_status("🔍 Looking for Google Ads...")
            
            # Selector untuk iklan Google Ads
            ads_selectors = [
                "a[href*='googleadservices.com']",
                "a[href*='doubleclick.net']",
                ".adsbygoogle",
                "[data-ad-client]",
                ".ad-container",
                ".ad-unit"
            ]
            
            for selector in ads_selectors:
                try:
                    ads = page.query_selector_all(selector)
                    if ads:
                        ad = random.choice(ads)
                        
                        # Scroll ke iklan
                        ad.scroll_into_view_if_needed()
                        time.sleep(2)
                        
                        # Klik iklan
                        if self.smart_click(page, ad):
                            self.update_status("🖱️ Clicked Google Ad, waiting...")
                            
                            # Tunggu di halaman iklan dengan durasi manusia
                            wait_time = random.uniform(8, 15)
                            self.update_status(f"⏳ Staying on ad page for {wait_time:.1f} seconds...")
                            time.sleep(wait_time)
                            
                            # Kembali ke website target
                            self.update_status("🔙 Returning to target website...")
                            page.go_back(wait_until='networkidle')
                            time.sleep(3)
                            return True
                except:
                    continue
            
            self.update_status("ℹ️ No Google Ads found")
            return False
            
        except Exception as e:
            self.update_status(f"❌ Error clicking ads: {str(e)}")
            return False
    
    def read_random_post(self, page, target_website):
        """Klik dan baca postingan acak dengan durasi manusia"""
        try:
            self.update_status("📖 Looking for random posts to read...")
            
            domain_patterns = self.extract_domain_patterns(target_website)
            
            # Cari link yang kemungkinan adalah postingan
            post_selectors = [
                "a[href*='/p/']",
                "a[href*='/post/']",
                "a[href*='/article/']",
                "a[href*='/blog/']",
                "a[href*='/202']",  # Postingan dengan tahun
                "a.entry-title",
                "a.post-title",
                "a.more-link"
            ]
            
            post_links = []
            for selector in post_selectors:
                try:
                    links = page.query_selector_all(selector)
                    for link in links:
                        try:
                            href = link.get_attribute('href')
                            if href and any(pattern in href for pattern in domain_patterns):
                                post_links.append(link)
                        except:
                            continue
                except:
                    continue
            
            if post_links:
                post_link = random.choice(post_links)
                link_text = post_link.text_content()[:50] if post_link.text_content() else "random post"
                self.update_status(f"📚 Reading: {link_text}...")
                
                # Klik postingan
                if self.smart_click(page, post_link):
                    # Tunggu halaman load
                    time.sleep(3)
                    
                    # Aktivitas membaca seperti manusia
                    self.update_status("👀 Simulating reading activity...")
                    
                    # Scroll pelan seperti membaca
                    self.reading_scroll_behavior(page)
                    
                    # Durasi membaca acak (seperti manusia)
                    read_time = random.uniform(20, 40)
                    self.update_status(f"⏳ Reading for {read_time:.1f} seconds...")
                    
                    # Selama membaca, lakukan micro-interactions
                    start_time = time.time()
                    while time.time() - start_time < read_time:
                        # Scroll kecil secara acak
                        if random.random() < 0.3:  # 30% chance untuk scroll kecil
                            current_pos = page.evaluate("window.pageYOffset")
                            page.evaluate(f"window.scrollTo(0, {current_pos + random.randint(100, 300)})")
                            time.sleep(random.uniform(2, 4))
                        
                        # Pause sebentar seperti manusia
                        time.sleep(random.uniform(1, 3))
                    
                    self.update_status("✅ Finished reading post")
                    
                    # Kembali ke halaman sebelumnya
                    page.go_back(wait_until='networkidle')
                    time.sleep(2)
                    return True
            
            self.update_status("ℹ️ No posts found to read")
            return False
            
        except Exception as e:
            self.update_status(f"❌ Error reading post: {str(e)}")
            return False
    
    def reading_scroll_behavior(self, page):
        """Scroll behavior khusus untuk membaca"""
        try:
            total_height = page.evaluate("() => document.body.scrollHeight")
            current_pos = 0
            
            # Scroll bertahap seperti manusia membaca
            while current_pos < total_height - 1000:
                scroll_amount = random.randint(200, 400)
                current_pos += scroll_amount
                
                page.evaluate(f"window.scrollTo(0, {current_pos})")
                
                # Variasi delay seperti manusia
                delay = random.uniform(1.5, 3.5)
                time.sleep(delay)
                
                # Kadang scroll mundur sedikit seperti manusia
                if random.random() < 0.2:
                    current_pos -= random.randint(50, 150)
                    page.evaluate(f"window.scrollTo(0, {current_pos})")
                    time.sleep(1)
            
        except Exception as e:
            self.update_status(f"Scroll error during reading: {str(e)}")
    
    def simulate_human_behavior(self, page, keyword, target_website):
        """Simulasi perilaku manusia dengan Playwright"""
        try:
            self.current_target_website = target_website
            
            # Strategy: Google search
            search_url = self.build_google_search_url(keyword)
            self.update_status(f"🔍 Searching: {keyword}")
            
            proxy_delay = self.get_proxy_delay()
            
            # Gunakan wait_until untuk menghindari timeout
            page.goto(search_url, wait_until='domcontentloaded')
            time.sleep(random.uniform(5 + proxy_delay, 8 + proxy_delay))
            
            # Handle Google Sorry page
            if not self.handle_google_sorry_page(page):
                self.update_status("🔄 Fallback to direct access...")
                return self.direct_website_access(page, target_website)
            
            # Tunggu hasil load
            try:
                page.wait_for_selector("div.g, .rc, .tF2Cxc", timeout=15000)
            except:
                self.update_status("⏳ Timeout waiting for results, continuing...")
            
            # Natural scroll
            self.natural_scroll_behavior(page)
            
            # Cari link target
            target_links = self.find_target_links_advanced(page, target_website)
            
            if target_links:
                return self.click_and_verify_target(page, target_links[0], target_website)
            else:
                self.update_status("🔗 No links found, direct access...")
                return self.direct_website_access(page, target_website)
                
        except Exception as e:
            self.update_status(f"❌ Simulation error: {str(e)}")
            return self.direct_website_access(page, target_website)
    
    def direct_website_access(self, page, target_website):
        """Akses website langsung"""
        try:
            self.update_status(f"🌐 Direct access: {target_website}")
            
            proxy_delay = self.get_proxy_delay()
            
            page.goto(target_website, wait_until='domcontentloaded')
            time.sleep(random.uniform(8 + proxy_delay, 12 + proxy_delay))
            
            if page.url:
                self.update_status("✅ Direct access successful")
                
                # 🔥 ACTIVITAS TAMBAHAN: Klik iklan Google Ads
                self.click_google_ads(page, target_website)
                
                # 🔥 ACTIVITAS TAMBAHAN: Klik postingan acak dan baca
                self.read_random_post(page, target_website)
                
                self.slow_scroll(page)
                self.click_random_internal_link(page, target_website)
                return True
            return False
        except Exception as e:
            self.update_status(f"❌ Direct access failed: {str(e)}")
            return False
    
    def click_random_internal_link(self, page, target_website):
        """Klik link internal acak"""
        try:
            domain_patterns = self.extract_domain_patterns(target_website)
            links = page.query_selector_all("a")
            
            internal_links = []
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and any(pattern in href for pattern in domain_patterns):
                        if href != page.url:
                            internal_links.append(link)
                except:
                    continue
            
            if internal_links:
                clicks = min(2, len(internal_links))
                for i in range(clicks):
                    try:
                        link = random.choice(internal_links)
                        link_text = link.text_content()[:50] if link.text_content() else "no text"
                        self.update_status(f"🔗 Click internal link: {link_text}...")
                        
                        if self.smart_click(page, link):
                            proxy_delay = self.get_proxy_delay()
                            time.sleep(random.uniform(5 + proxy_delay, 8 + proxy_delay))
                            self.slow_scroll(page)
                            
                            if random.choice([True, False]):
                                page.go_back(wait_until='domcontentloaded')
                                time.sleep(2)
                    except:
                        continue
        except Exception as e:
            self.update_status(f"Error clicking internal links: {str(e)}")
    
    def slow_scroll(self, page):
        """Scroll pelan seperti manusia"""
        try:
            total_height = page.evaluate("() => document.body.scrollHeight")
            viewport_height = page.evaluate("() => window.innerHeight")
            current_position = 0
            
            scrolls = random.randint(3, 6)
            for i in range(scrolls):
                scroll_amount = random.randint(300, 600)
                current_position += scroll_amount
                
                if current_position >= total_height:
                    current_position = total_height - viewport_height
                
                page.evaluate(f"window.scrollTo(0, {current_position})")
                
                proxy_delay = self.get_proxy_delay() / 2
                time.sleep(random.uniform(2 + proxy_delay, 4 + proxy_delay))
                
            # Scroll back to top
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            
        except Exception as e:
            self.update_status(f"Scroll error: {str(e)}")
    
    def clear_cache(self, context):
        """Bersihkan cache dan cookies"""
        try:
            context.clear_cookies()
            self.update_status("🧹 Cache and cookies cleared")
        except Exception as e:
            self.update_status(f"Error clearing cache: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles, proxy_list):
        """Jalankan semua cycles dengan Playwright"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        if not keywords:
            keywords = self.generate_keywords_from_url(target_website)
            self.update_status(f"Generated keywords: {', '.join(keywords[:5])}...")
        
        working_proxies = self.get_working_proxies(proxy_list) if proxy_list else []
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"🔄 Starting cycle {self.current_cycle}/{cycles}")
            
            # Rotate proxies
            current_proxy_list = working_proxies if working_proxies else []
            if current_proxy_list and cycle > 0:
                random.shuffle(current_proxy_list)
            
            playwright, browser, context, page = self.setup_browser(current_proxy_list)
            if not browser:
                self.update_status("❌ Failed to setup browser, skipping cycle")
                continue
            
            try:
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(page, keyword, target_website)
                
                if success:
                    self.update_status(f"✅ Cycle {self.current_cycle} completed successfully")
                else:
                    self.update_status(f"⚠️ Cycle {self.current_cycle} completed with issues")
                
                self.clear_cache(context)
                
            except Exception as e:
                self.update_status(f"❌ Cycle {self.current_cycle} error: {str(e)}")
            finally:
                try:
                    context.close()
                    browser.close()
                    playwright.stop()
                except:
                    pass
            
            if cycle < cycles - 1 and self.is_running:
                extra_delay = self.get_proxy_delay()
                total_delay = delay_between_cycles + extra_delay
                self.update_status(f"⏳ Waiting {total_delay} seconds...")
                for i in range(total_delay):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        self.is_running = False
        self.update_status("🎉 All cycles completed!")

# Global instance
booster = SEOTrafficBooster()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Connected to SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles,
        'current_proxy': booster.current_proxy
    })

@socketio.on('start_cycles')
def handle_start_cycles(data):
    if booster.is_running:
        emit('error', {'message': 'Booster is already running!'})
        return
    
    keywords = [k.strip() for k in data['keywords'].split('\n') if k.strip()]
    target_website = data['website'].strip()
    cycles = int(data['cycles'])
    delay = int(data['delay'])
    proxy_list = [p.strip() for p in data['proxies'].split('\n') if p.strip()] 
    
    if not target_website:
        emit('error', {'message': 'Please enter target website!'})
        return
    
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay, proxy_list)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster started!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'Stopping booster...'})

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
