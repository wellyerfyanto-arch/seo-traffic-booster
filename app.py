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
from urllib.parse import urlparse, urlunparse
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
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
    
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
            domain = parsed_url.netloc.replace('www.', '').replace('.com', '').replace('.org', '').replace('.net', '')
            path_parts = parsed_url.path.strip('/').split('/')
            
            keywords = []
            
            # Keyword dari domain
            if domain:
                domain_keywords = domain.split('.')[0].split('-')
                keywords.extend([kw.capitalize() for kw in domain_keywords if kw])
            
            # Keyword dari path
            for part in path_parts:
                if part and not part.isdigit() and len(part) > 2:
                    part_keywords = part.split('-')
                    keywords.extend([kw.capitalize() for kw in part_keywords if kw])
            
            # Tambahkan keyword umum berdasarkan konten
            if not keywords:
                keywords = ["technology", "news", "blog", "articles", "updates"]
            
            # Buat variasi keyword
            final_keywords = []
            for kw in keywords[:5]:  # Ambil maksimal 5 keyword utama
                final_keywords.extend([
                    kw,
                    f"what is {kw}",
                    f"{kw} news",
                    f"latest {kw}",
                    f"best {kw}",
                    f"{kw} guide"
                ])
            
            return list(set(final_keywords))[:10]  # Hapus duplikat dan batasi 10 keyword
        
        except Exception as e:
            self.update_status(f"Error generating keywords: {str(e)}")
            return ["technology", "digital news", "web updates", "online content", "internet guide"]
    
    def build_google_search_url(self, keyword, target_website):
        """Bangun URL pencarian Google langsung dengan site: operator"""
        # Encode keyword untuk URL
        encoded_keyword = requests.utils.quote(keyword)
        
        # Parse domain dari target website
        domain = urlparse(target_website).netloc.replace('www.', '')
        
        # Gunakan site: operator untuk meningkatkan akurasi
        search_query = f"site:{domain} {encoded_keyword}"
        
        return f"https://www.google.com/search?q={search_query}&gbv=1"
    
    def extract_domain_variations(self, url):
        """Ekstrak berbagai variasi domain untuk pencarian yang lebih akurat"""
        parsed = urlparse(url)
        domain = parsed.netloc
        
        variations = []
        
        # Variasi dasar
        variations.append(domain)  # www.example.com
        variations.append(domain.replace('www.', ''))  # example.com
        
        # Variasi dengan dan tanpa subdomain
        if domain.startswith('www.'):
            variations.append(domain[4:])  # example.com
        else:
            variations.append(f"www.{domain}")  # www.example.com
        
        # Ekstrak nama domain utama (tanpa TLD)
        domain_parts = domain.replace('www.', '').split('.')
        if len(domain_parts) >= 2:
            main_domain = domain_parts[-2]  # example dari example.com
            variations.append(main_domain)
        
        return list(set(variations))  # Hapus duplikat
    
    def find_target_links(self, driver, target_website):
        """Mencari link target dengan berbagai strategi"""
        domain_variations = self.extract_domain_variations(target_website)
        
        # Strategi 1: Cari dengan berbagai variasi domain
        for domain_var in domain_variations:
            xpath = f"//a[contains(@href, '{domain_var}')]"
            links = driver.find_elements(By.XPATH, xpath)
            if links:
                self.update_status(f"Ditemukan {len(links)} link dengan domain: {domain_var}")
                return links
        
        # Strategi 2: Cari semua link dan filter manual
        self.update_status("Mencari link dengan strategi alternatif...")
        all_links = driver.find_elements(By.TAG_NAME, "a")
        target_links = []
        
        for link in all_links:
            href = link.get_attribute('href')
            if href:
                for domain_var in domain_variations:
                    if domain_var in href:
                        target_links.append(link)
                        break
        
        if target_links:
            self.update_status(f"Ditemukan {len(target_links)} link dengan filter manual")
            return target_links
        
        # Strategi 3: Cari di hasil search (biasanya di div dengan class g)
        self.update_status("Mencari di struktur hasil Google...")
        search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")
        
        for result in search_results:
            try:
                links = result.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute('href')
                    if href:
                        for domain_var in domain_variations:
                            if domain_var in href:
                                target_links.append(link)
                                break
            except:
                continue
        
        return target_links
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia dengan pencarian langsung"""
        try:
            # Build Google search URL langsung dengan site: operator
            search_url = self.build_google_search_url(keyword, target_website)
            
            self.update_status(f"Membuka pencarian Google: {keyword}")
            driver.get(search_url)
            time.sleep(random.uniform(3, 5))
            
            # Scroll sedikit untuk memuat semua hasil
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            
            self.update_status(f"Mencari: {target_website}")
            
            # Cari link target dengan berbagai strategi
            target_links = self.find_target_links(driver, target_website)
            
            if target_links:
                # Pilih link yang paling mungkin benar
                target_link = target_links[0]
                
                # Verifikasi link sebelum klik
                link_href = target_link.get_attribute('href')
                self.update_status(f"Memilih link: {link_href[:80]}...")
                
                # Scroll ke element sebelum klik
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", target_link)
                time.sleep(random.uniform(1, 2))
                
                # Klik menggunakan JavaScript untuk menghindari masalah interaksi
                driver.execute_script("arguments[0].click();", target_link)
                self.update_status("Berhasil klik website target")
                time.sleep(random.uniform(5, 8))  # Tunggu lebih lama untuk loading
                
                # Verifikasi kita sudah di website yang benar
                current_url = driver.current_url
                domain_variations = self.extract_domain_variations(target_website)
                is_correct_site = any(var in current_url for var in domain_variations)
                
                if not is_correct_site:
                    self.update_status("Mungkin tidak di website target, mencoba navigasi manual...")
                    # Coba akses langsung
                    driver.get(target_website)
                    time.sleep(random.uniform(3, 5))
                
                self.update_status("Scrolling ke bawah")
                self.slow_scroll(driver)
                
                # Kembali ke atas
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                # Coba klik link internal acak
                current_domain = urlparse(driver.current_url).netloc
                links = driver.find_elements(By.TAG_NAME, "a")
                internal_links = [
                    link for link in links 
                    if link.get_attribute('href') and current_domain in link.get_attribute('href')
                ]
                
                if internal_links:
                    try:
                        random_link = random.choice(internal_links[:10])  # Batasi pilihan
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", random_link)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", random_link)
                        self.update_status("Klik artikel random")
                        time.sleep(random.uniform(4, 6))
                        
                        self.update_status("Scrolling artikel")
                        self.scroll_for_duration(driver, 10)  # Kurangi durasi
                    except Exception as e:
                        self.update_status(f"Tidak bisa klik artikel: {str(e)}")
                
                return True
            else:
                self.update_status("Website target tidak ditemukan di hasil search, mencoba akses langsung...")
                # Fallback: akses website langsung
                try:
                    driver.get(target_website)
                    time.sleep(random.uniform(5, 8))
                    self.update_status("Akses langsung berhasil")
                    
                    # Lakukan aktivitas browsing biasa
                    self.update_status("Scrolling website")
                    self.slow_scroll(driver)
                    
                    return True
                except Exception as e:
                    self.update_status(f"Gagal akses langsung: {str(e)}")
                    return False
                
        except Exception as e:
            self.update_status(f"Error simulasi: {str(e)}")
            # Fallback ke akses langsung
            try:
                driver.get(target_website)
                time.sleep(random.uniform(5, 8))
                self.update_status("Fallback: Akses langsung berhasil")
                return True
            except:
                return False
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        try:
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            current_position = 0
            
            while current_position < total_height:
                scroll_amount = random.randint(200, 400)
                current_position += scroll_amount
                
                # Jangan scroll melebihi total height
                if current_position > total_height:
                    current_position = total_height
                
                driver.execute_script(f"window.scrollTo(0, {current_position});")
                
                # Kadang berhenti sebentar
                if random.random() > 0.7:
                    time.sleep(random.uniform(1, 3))
                else:
                    time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            self.update_status(f"Error saat scroll: {str(e)}")
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-150, -80, 80, 150, 200])
            driver.execute_script(f"window.scrollBy(0, {scroll_direction});")
            time.sleep(random.uniform(0.5, 2))
    
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
            self.update_status(f"Generated keywords: {', '.join(keywords)}")
        
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
                
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} sukses")
                else:
                    self.update_status(f"Cycle {self.current_cycle} ada masalah")
                
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} error: {str(e)}")
            finally:
                try:
                    driver.quit()
                except:
                    pass
            
            if cycle < cycles - 1 and self.is_running:
                self.update_status(f"Tunggu {delay_between_cycles} detik")
                for i in range(delay_between_cycles):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        self.is_running = False
        self.update_status("Semua cycle selesai!")

# Global instance
booster = SEOTrafficBooster()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Terhubung ke SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles,
        'current_proxy': booster.current_proxy
    })

@socketio.on('start_cycles')
def handle_start_cycles(data):
    if booster.is_running:
        emit('error', {'message': 'Booster sedang berjalan!'})
        return
    
    keywords = [k.strip() for k in data['keywords'].split('\n') if k.strip()]
    target_website = data['website'].strip()
    cycles = int(data['cycles'])
    delay = int(data['delay'])
    proxy_list = [p.strip() for p in data['proxies'].split('\n') if p.strip()] 
    
    if not target_website:
        emit('error', {'message': 'Masukkan website target!'})
        return
    
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay, proxy_list)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster mulai!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'Menghentikan booster...'})

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
