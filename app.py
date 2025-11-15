import time
import random
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import requests
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from urllib.parse import urlparse, quote_plus
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seo_traffic_booster_secret'
socketio = SocketIO(app) 

class SEOTrafficBooster:
    def __init__(self):
        self.ua = UserAgent()
        self.is_running = False
        self.current_status = "Ready"
        self.current_cycle = 0
        self.total_cycles = 0
        self.current_proxy = None
        
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
        
    def setup_driver(self, proxy_list):
        """Setup Chrome driver dengan konfigurasi dan proxy"""
        chrome_options = Options()
    
        # Random User Agent
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
    
        # Proxy settings jika ada
        if proxy_list:
            proxy = random.choice(proxy_list)
            self.current_proxy = proxy
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
            self.update_status(f"Menggunakan proxy: {proxy}")
        else:
            self.current_proxy = None
            self.update_status("Menjalankan tanpa proxy")
    
        # Chrome options untuk menghindari deteksi
        chrome_options.add_argument('--headless=new')  # Menggunakan headless baru
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
    
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.update_status(f"Error setting up driver: {str(e)}")
            return None
    
    def test_proxy(self, proxy):
        """Test jika proxy berfungsi"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(test_url, proxies=proxies, timeout=5)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def get_working_proxies(self, proxy_list):
        """Filter proxy yang berfungsi"""
        working_proxies = []
        self.update_status(f"Testing {len(proxy_list)} proxies...")
        
        for proxy in proxy_list:
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
        
        self.update_status(f"Found {len(working_proxies)} working proxies")
        return working_proxies
    
    def generate_keywords_from_url(self, url):
        """Generate keyword SEO otomatis dari URL"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            
            # Untuk blogspot, ambil nama subdomain
            if 'blogspot.com' in domain:
                blog_name = domain.replace('.blogspot.com', '')
                keywords = [
                    blog_name,
                    f"{blog_name} blog",
                    f"{blog_name} articles",
                    f"{blog_name} posts",
                    "blogspot",
                    "blogger",
                    "blog"
                ]
            else:
                # Untuk domain biasa
                domain_keywords = domain.replace('.com', '').replace('.org', '').replace('.net', '').split('.')
                keywords = []
                for kw in domain_keywords:
                    if kw and len(kw) > 2:
                        keywords.extend([
                            kw,
                            f"{kw} blog",
                            f"{kw} website",
                            f"{kw} online"
                        ])
            
            # Tambahkan variasi
            final_keywords = []
            for kw in keywords[:6]:
                final_keywords.extend([
                    kw,
                    f"site:{domain} {kw}",
                    f"{kw} latest",
                    f"{kw} update",
                    f"what is {kw}",
                    f"about {kw}"
                ])
            
            return list(set(final_keywords))[:15]
        
        except Exception as e:
            self.update_status(f"Error generating keywords: {str(e)}")
            return ["blog", "articles", "posts", "website", "online content"]
    
    def build_google_search_url(self, keyword):
        """Bangun URL pencarian Google langsung"""
        # Encode keyword untuk URL
        encoded_keyword = quote_plus(keyword)
        return f"https://www.google.com/search?q={encoded_keyword}"
    
    def extract_domain_patterns(self, url):
        """Ekstrak berbagai pola domain untuk pencarian yang lebih akurat"""
        parsed = urlparse(url)
        full_domain = parsed.netloc
        clean_domain = full_domain.replace('www.', '')
        
        patterns = []
        
        # Pattern dasar
        patterns.append(clean_domain)  # cryptoajah.blogspot.com
        patterns.append(full_domain)   # www.cryptoajah.blogspot.com
        
        # Untuk blogspot, tambahkan pattern khusus
        if 'blogspot.com' in clean_domain:
            blog_name = clean_domain.replace('.blogspot.com', '')
            patterns.append(blog_name)  # cryptoajah
            patterns.append(f"{blog_name}.blogspot.com")
            patterns.append(f"www.{blog_name}.blogspot.com")
            # Pattern untuk link blogspot yang umum
            patterns.append(f"https://{blog_name}.blogspot.com")
            patterns.append(f"https://{blog_name}.blogspot.com/")
            patterns.append(f"http://{blog_name}.blogspot.com")
        
        # Pattern path jika ada
        if parsed.path and parsed.path != '/':
            path_clean = parsed.path.strip('/')
            patterns.append(f"{clean_domain}/{path_clean}")
            patterns.append(f"{full_domain}/{path_clean}")
        
        return list(set(patterns))
    
    def find_target_links_advanced(self, driver, target_website):
        """Mencari link target dengan strategi yang lebih advanced"""
        domain_patterns = self.extract_domain_patterns(target_website)
        found_links = []
        
        self.update_status(f"Mencari dengan {len(domain_patterns)} pola domain...")
        
        # Strategi 1: Cari dengan CSS selector hasil Google
        selectors = [
            "div.g a",  # Hasil utama Google
            "a[href*='blogspot']",  # Link blogspot khusus
            "h3 a",  # Heading hasil
            ".rc a",  # Result container
            ".r a",   # Result
            "a[ping]" # Link dengan ping attribute (khas Google)
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    href = elem.get_attribute('href')
                    if href:
                        for pattern in domain_patterns:
                            if pattern in href:
                                found_links.append(elem)
                                break
                if found_links:
                    self.update_status(f"Ditemukan {len(found_links)} link dengan selector: {selector}")
                    break
            except Exception as e:
                continue
        
        # Strategi 2: Cari semua link dan filter
        if not found_links:
            self.update_status("Mencari semua link di halaman...")
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href:
                        for pattern in domain_patterns:
                            if pattern in href.lower():
                                found_links.append(link)
                                break
                except:
                    continue
        
        # Strategi 3: Cari dengan teks yang relevan
        if not found_links:
            self.update_status("Mencari dengan teks link...")
            link_texts = ["blog", "website", "site", "visit", "here", "read more", "continue"]
            for text in link_texts:
                try:
                    links = driver.find_elements(By.PARTIAL_LINK_TEXT, text)
                    for link in links:
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
    
    def smart_click(self, driver, element):
        """Klik element dengan cara yang lebih smart"""
        try:
            # Scroll ke element
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
            
            # Coba klik dengan JavaScript
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            try:
                # Coba klik normal
                element.click()
                return True
            except:
                try:
                    # Coba dengan ActionChains
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(driver)
                    actions.move_to_element(element).click().perform()
                    return True
                except:
                    return False
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia dengan pencarian langsung"""
        try:
            # Build Google search URL
            search_url = self.build_google_search_url(keyword)
            
            self.update_status(f"Membuka pencarian Google: {keyword}")
            driver.get(search_url)
            time.sleep(random.uniform(4, 6))
            
            # Tunggu hasil load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll bertahap
            self.update_status("Scrolling hasil pencarian...")
            for i in range(3):
                driver.execute_script(f"window.scrollTo(0, {500 * (i + 1)});")
                time.sleep(1)
            
            self.update_status(f"Mencari: {target_website}")
            
            # Cari link target
            target_links = self.find_target_links_advanced(driver, target_website)
            
            if target_links:
                self.update_status(f"Found {len(target_links)} potential links")
                
                # Pilih link yang paling relevan
                target_link = target_links[0]
                link_href = target_link.get_attribute('href')
                self.update_status(f"Selected: {link_href[:100]}...")
                
                # Klik link
                if self.smart_click(driver, target_link):
                    self.update_status("Berhasil klik website target")
                    time.sleep(random.uniform(6, 10))
                    
                    # Verifikasi kita di website yang benar
                    current_url = driver.current_url
                    domain_patterns = self.extract_domain_patterns(target_website)
                    is_correct_site = any(pattern in current_url for pattern in domain_patterns)
                    
                    if is_correct_site:
                        self.update_status("Berhasil sampai di website target")
                        
                        # Lakukan aktivitas manusia
                        self.update_status("Browsing website...")
                        self.slow_scroll(driver)
                        
                        # Klik internal link jika memungkinkan
                        self.click_random_internal_link(driver, target_website)
                        
                        return True
                    else:
                        self.update_status("Redirected to different site, trying direct access...")
                        # Coba akses langsung
                        return self.direct_website_access(driver, target_website)
                else:
                    self.update_status("Gagal klik link, coba akses langsung")
                    return self.direct_website_access(driver, target_website)
            else:
                self.update_status("Tidak menemukan link di hasil search, akses langsung...")
                return self.direct_website_access(driver, target_website)
                
        except Exception as e:
            self.update_status(f"Error during search: {str(e)}")
            return self.direct_website_access(driver, target_website)
    
    def direct_website_access(self, driver, target_website):
        """Akses website langsung tanpa melalui search"""
        try:
            self.update_status(f"Mengakses website langsung: {target_website}")
            driver.get(target_website)
            time.sleep(random.uniform(8, 12))
            
            # Verifikasi berhasil load
            if driver.current_url:
                self.update_status("Berhasil akses website langsung")
                self.slow_scroll(driver)
                self.click_random_internal_link(driver, target_website)
                return True
            else:
                return False
        except Exception as e:
            self.update_status(f"Gagal akses langsung: {str(e)}")
            return False
    
    def click_random_internal_link(self, driver, target_website):
        """Klik link internal acak"""
        try:
            domain_patterns = self.extract_domain_patterns(target_website)
            links = driver.find_elements(By.TAG_NAME, "a")
            
            internal_links = []
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and any(pattern in href for pattern in domain_patterns):
                        # Skip link yang sama dengan current URL
                        if href != driver.current_url:
                            internal_links.append(link)
                except:
                    continue
            
            if internal_links:
                # Pilih maksimal 2 link internal untuk diklik
                clicks = min(2, len(internal_links))
                for i in range(clicks):
                    try:
                        link = random.choice(internal_links)
                        link_text = link.text[:50] if link.text else "no text"
                        self.update_status(f"Klik internal link: {link_text}...")
                        
                        if self.smart_click(driver, link):
                            time.sleep(random.uniform(5, 8))
                            self.slow_scroll(driver)
                            # Kembali ke halaman sebelumnya atau tetap di halaman baru
                            if random.choice([True, False]):
                                driver.back()
                                time.sleep(2)
                    except:
                        continue
        except Exception as e:
            self.update_status(f"Error clicking internal links: {str(e)}")
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        try:
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            current_position = 0
            
            scrolls = random.randint(3, 6)
            for i in range(scrolls):
                scroll_amount = random.randint(300, 600)
                current_position += scroll_amount
                
                if current_position >= total_height:
                    current_position = total_height - viewport_height
                
                driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(2, 4))
                
            # Scroll kembali ke atas
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            self.update_status(f"Error during scroll: {str(e)}")
    
    def clear_cache(self, driver):
        """Bersihkan cache dan cookies"""
        try:
            driver.delete_all_cookies()
            self.update_status("Cache cleared")
        except Exception as e:
            self.update_status(f"Error clear cache: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles, proxy_list):
        """Jalankan semua cycles"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        # Generate keywords otomatis jika tidak ada yang diinput
        if not keywords:
            keywords = self.generate_keywords_from_url(target_website)
            self.update_status(f"Generated keywords: {', '.join(keywords[:5])}...")
        
        working_proxies = self.get_working_proxies(proxy_list) if proxy_list else []
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Memulai cycle {self.current_cycle}/{cycles}")
            
            current_proxy_list = working_proxies if working_proxies else []
            
            driver = self.setup_driver(current_proxy_list)
            if not driver:
                self.update_status("Gagal setup driver, skip cycle")
                continue
            
            try:
                # Cek IP saat ini (Opsional)
                try:
                    driver.get("https://httpbin.org/ip")
                    time.sleep(2)
                    self.update_status("IP check completed")
                except:
                    self.update_status("IP check skipped")
                
                keyword = random.
