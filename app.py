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
import eventlet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seo_traffic_booster_secret'
socketio = SocketIO(app, async_mode='eventlet')

class SEOTrafficBooster:
    def __init__(self):
        self.ua = UserAgent()
        self.is_running = False
        self.current_status = "Ready"
        self.current_cycle = 0
        self.total_cycles = 0
        self.current_proxy = None
        
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
    
    def test_proxy(self, proxy):
        """Test jika proxy berfungsi"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def get_working_proxies(self, proxy_list):
        """Filter proxy yang berfungsi"""
        working_proxies = []
        self.update_status(f"Testing {len(proxy_list)} proxies...")
        
        for proxy in proxy_list[:10]:  # Test 10 proxy pertama saja
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
        
        self.update_status(f"Found {len(working_proxies)} working proxies")
        return working_proxies
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia"""
        try:
            # Step 1: Buka Google
            self.update_status("Membuka Google Search")
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            # Step 2: Input keyword
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            self.update_status(f"Searching: {keyword}")
            
            # Ketik seperti manusia
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            search_box.submit()
            time.sleep(random.uniform(3, 5))
            
            # Step 3: Cari dan klik website target
            self.update_status(f"Mencari: {target_website}")
            target_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            
            if target_links:
                target_link = target_links[0]
                target_link.click()
                self.update_status("Berhasil klik website target")
                time.sleep(random.uniform(3, 5))
                
                # Step 4: Scroll pelan ke bawah
                self.update_status("Scrolling ke bawah")
                self.slow_scroll(driver)
                
                # Step 5: Kembali ke atas
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                # Step 6: Cari dan klik postingan acak
                links = driver.find_elements(By.TAG_NAME, "a")
                if links:
                    try:
                        random_link = random.choice(links)
                        random_link.click()
                        self.update_status("Klik artikel random")
                        time.sleep(random.uniform(3, 5))
                        
                        # Step 7: Scroll selama beberapa detik
                        self.update_status("Scrolling artikel")
                        self.scroll_for_duration(driver, 15)
                        
                    except Exception as e:
                        self.update_status(f"Tidak bisa klik artikel: {str(e)}")
                
                return True
            else:
                self.update_status("Website target tidak ditemukan di hasil search")
                return False
                
        except Exception as e:
            self.update_status(f"Error simulasi: {str(e)}")
            return False
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        while current_position < total_height:
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.5))
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-100, -50, 50, 100, 150])
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
        
        # Filter proxy yang berfungsi
        working_proxies = self.get_working_proxies(proxy_list) if proxy_list else []
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Memulai cycle {self.current_cycle}/{cycles}")
            
            # Gunakan proxy yang berbeda setiap cycle jika tersedia
            current_proxy_list = working_proxies if working_proxies else []
            
            driver = self.setup_driver(current_proxy_list)
            if not driver:
                self.update_status("Gagal setup driver, skip cycle")
                continue
            
            try:
                # Cek IP saat ini
                try:
                    driver.get("https://httpbin.org/ip")
                    time.sleep(2)
                    self.update_status("IP check completed")
                except:
                    self.update_status("IP check skipped")
                
                # Jalankan simulasi
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} sukses")
                else:
                    self.update_status(f"Cycle {self.current_cycle} ada masalah")
                
                # Bersihkan cache
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} error: {str(e)}")
            finally:
                try:
                    driver.quit()
                except:
                    pass
            
            # Delay antara cycles
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Masukkan keywords dan website target!'})
        return
    
    # Jalankan di thread terpisah
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
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)        chrome_options.add_argument('--no-sandbox')
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
    
    def update_status(self, message):
        """Update status dan kirim ke UI"""
        self.current_status = message
        timestamp = time.strftime("%H:%M:%S")
        socketio.emit('status_update', {
            'message': f"[{timestamp}] {message}",
            'cycle': self.current_cycle,
            'total_cycles': self.total_cycles
        })
        print(f"[{timestamp}] {message}")
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia"""
        try:
            # Step 1: Buka Google
            self.update_status("Membuka Google Search")
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            # Step 2: Input keyword
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            self.update_status(f"Searching: {keyword}")
            
            # Ketik seperti manusia
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            search_box.submit()
            time.sleep(random.uniform(3, 5))
            
            # Step 3: Cari dan klik website target
            self.update_status(f"Mencari: {target_website}")
            target_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            
            if target_links:
                target_link = target_links[0]
                target_link.click()
                self.update_status("Berhasil klik website target")
                time.sleep(random.uniform(3, 5))
                
                # Step 4: Scroll pelan ke bawah
                self.update_status("Scrolling ke bawah")
                self.slow_scroll(driver)
                
                # Step 5: Kembali ke atas
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                # Step 6: Cari dan klik postingan acak
                links = driver.find_elements(By.TAG_NAME, "a")
                if links:
                    try:
                        random_link = random.choice(links)
                        random_link.click()
                        self.update_status("Klik artikel random")
                        time.sleep(random.uniform(3, 5))
                        
                        # Step 7: Scroll selama beberapa detik
                        self.update_status("Scrolling artikel")
                        self.scroll_for_duration(driver, 15)
                        
                    except Exception as e:
                        self.update_status(f"Tidak bisa klik artikel: {str(e)}")
                
                return True
            else:
                self.update_status("Website target tidak ditemukan di hasil search")
                return False
                
        except Exception as e:
            self.update_status(f"Error simulasi: {str(e)}")
            return False
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        while current_position < total_height:
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.5))
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-100, -50, 50, 100, 150])
            driver.execute_script(f"window.scrollBy(0, {scroll_direction});")
            time.sleep(random.uniform(0.5, 2))
    
    def clear_cache(self, driver):
        """Bersihkan cache dan cookies"""
        try:
            driver.delete_all_cookies()
            self.update_status("Cache cleared")
        except Exception as e:
            self.update_status(f"Error clear cache: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles):
        """Jalankan semua cycles"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Memulai cycle {self.current_cycle}/{cycles}")
            
            driver = self.setup_driver()
            if not driver:
                self.update_status("Gagal setup driver, skip cycle")
                continue
            
            try:
                # Jalankan simulasi
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} sukses")
                else:
                    self.update_status(f"Cycle {self.current_cycle} ada masalah")
                
                # Bersihkan cache
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} error: {str(e)}")
            finally:
                try:
                    driver.quit()
                except:
                    pass
            
            # Delay antara cycles
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
        'total_cycles': booster.total_cycles
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Masukkan keywords dan website target!'})
        return
    
    # Jalankan di thread terpisah
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster mulai!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'Menghentikan booster...'})

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=US',
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        ]
        
        for api_url in api_sources:
            try:
                headers = {'User-Agent': self.ua.random}
                response = requests.get(api_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Parse response text untuk mendapatkan proxy
                    lines = response.text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line and not line.startswith('#'):
                            # Validasi format IP:PORT
                            parts = line.split(':')
                            if len(parts) == 2 and parts[1].isdigit():
                                all_proxies.append(line)
                                
                    self.update_status(f"Got {len(lines)} proxies from {api_url}")
                    
            except Exception as e:
                self.update_status(f"Error from {api_url}: {str(e)}")
                continue
        
        # Jika tidak ada proxy yang didapat, gunakan fallback
        if not all_proxies:
            all_proxies = self.get_fallback_proxies()
        
        return list(set(all_proxies))[:50]

    def get_fallback_proxies(self):
        """Fallback proxy list jika API tidak bekerja"""
        common_proxies = [
            "34.82.224.175:3128", 
            "35.185.196.38:3128", 
            "104.154.143.77:3128",
            "35.224.246.249:3128", 
            "34.83.225.238:3128"
        ]
        return common_proxies
    
    def test_proxy(self, proxy):
        """Test jika proxy berfungsi"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def get_working_proxy(self):
        """Dapatkan proxy yang berfungsi"""
        if not self.proxies:
            self.proxies = self.get_auto_proxies()
            self.update_status(f"Found {len(self.proxies)} proxies")
        
        working_proxies = []
        for proxy in self.proxies[:10]:
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
        
        if working_proxies:
            return random.choice(working_proxies)
        else:
            self.update_status("No working proxies found, continuing without proxy")
            return None
    
    def setup_driver(self):
        """Setup Chrome driver dengan konfigurasi"""
        chrome_options = Options()
        
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        proxy = self.get_working_proxy()
        if proxy:
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
            self.update_status(f"Using proxy: {proxy}")
        
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.update_status(f"Error setting up driver: {str(e)}")
            return None
    
    def update_status(self, message):
        """Update status dan kirim ke UI"""
        self.current_status = message
        timestamp = time.strftime("%H:%M:%S")
        socketio.emit('status_update', {
            'message': f"[{timestamp}] {message}",
            'cycle': self.current_cycle,
            'total_cycles': self.total_cycles
        })
        print(f"[{timestamp}] {message}")
    
    def check_ip_leak(self, driver):
        """Cek kebocoran IP"""
        try:
            driver.get("https://api.ipify.org")
            ip_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            current_ip = ip_element.text
            self.update_status(f"IP Check: {current_ip}")
            return True
        except Exception as e:
            self.update_status(f"IP leak check failed: {str(e)}")
            return False
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia"""
        try:
            self.update_status("Opening Google Search")
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            self.update_status(f"Searching for: {keyword}")
            
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            search_box.submit()
            time.sleep(random.uniform(3, 5))
            
            self.update_status(f"Looking for: {target_website}")
            target_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            
            if target_links:
                target_link = target_links[0]
                target_link.click()
                self.update_status("Clicked target website")
                time.sleep(random.uniform(3, 5))
                
                self.update_status("Scrolling to bottom")
                self.slow_scroll(driver)
                
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                links = driver.find_elements(By.TAG_NAME, "a")
                article_links = [link for link in links if self.is_article_link(link)]
                
                if article_links:
                    random_article = random.choice(article_links)
                    try:
                        random_article.click()
                        self.update_status("Clicked random article")
                        time.sleep(random.uniform(3, 5))
                        
                        self.update_status("Scrolling article for 20 seconds")
                        self.scroll_for_duration(driver, 20)
                        
                    except Exception as e:
                        self.update_status(f"Could not click article: {str(e)}")
                
                return True
            else:
                self.update_status("Target website not found in search results")
                return False
                
        except Exception as e:
            self.update_status(f"Simulation error: {str(e)}")
            return False
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        while current_position < total_height:
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Kadang berhenti sebentar
            if random.random() < 0.2:
                time.sleep(random.uniform(1, 3))
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-100, -50, 50, 100, 150])
            driver.execute_script(f"window.scrollBy(0, {scroll_direction});")
            time.sleep(random.uniform(0.5, 2))
    
    def is_article_link(self, link):
        """Cek jika link kemungkinan adalah artikel"""
        href = link.get_attribute('href')
        text = link.text.strip()
        
        if not href or not text:
            return False
        
        article_indicators = ['blog', 'article', 'post', 'news', '2023', '2024', 'read', 'story']
        href_lower = href.lower()
        text_lower = text.lower()
        
        return any(indicator in href_lower or indicator in text_lower for indicator in article_indicators)
    
    def clear_cache(self, driver):
        """Bersihkan cache dan cookies"""
        try:
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            driver.delete_all_cookies()
            self.update_status("Cache cleared")
        except Exception as e:
            self.update_status(f"Cache clear error: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles):
        """Jalankan semua cycles"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Starting cycle {self.current_cycle}/{cycles}")
            
            driver = self.setup_driver()
            if not driver:
                self.update_status("Failed to setup driver, skipping cycle")
                continue
            
            try:
                if not self.check_ip_leak(driver):
                    self.update_status("IP leak detected, skipping cycle")
                    continue
                
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} completed successfully")
                else:
                    self.update_status(f"Cycle {self.current_cycle} completed with issues")
                
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} failed: {str(e)}")
            finally:
                driver.quit()
            
            if cycle < cycles - 1 and self.is_running:
                self.update_status(f"Waiting {delay_between_cycles} seconds before next cycle")
                for i in range(delay_between_cycles):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        self.is_running = False
        self.update_status("All cycles completed!")

# Global instance
booster = SEOTrafficBooster()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Connected to SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Please provide keywords and target website!'})
        return
    
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster started successfully!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'SEO Booster stopping...'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=US',
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        ]
        
        for api_url in api_sources:
            try:
                headers = {'User-Agent': self.ua.random}
                response = requests.get(api_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Parse response text untuk mendapatkan proxy
                    lines = response.text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line and not line.startswith('#'):
                            # Validasi format IP:PORT
                            parts = line.split(':')
                            if len(parts) == 2 and parts[1].isdigit():
                                all_proxies.append(line)
                                
                    self.update_status(f"Got {len(lines)} proxies from {api_url}")
                    
            except Exception as e:
                self.update_status(f"Error from {api_url}: {str(e)}")
                continue
        
        # Jika tidak ada proxy yang didapat, gunakan fallback
        if not all_proxies:
            all_proxies = self.get_fallback_proxies()
        
        return list(set(all_proxies))[:50]

    def get_fallback_proxies(self):
        """Fallback proxy list jika API tidak bekerja"""
        common_proxies = [
            "34.82.224.175:3128", 
            "35.185.196.38:3128", 
            "104.154.143.77:3128",
            "35.224.246.249:3128", 
            "34.83.225.238:3128"
        ]
        return common_proxies
    
    def test_proxy(self, proxy):
        """Test jika proxy berfungsi"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def get_working_proxy(self):
        """Dapatkan proxy yang berfungsi"""
        if not self.proxies:
            self.proxies = self.get_auto_proxies()
            self.update_status(f"Found {len(self.proxies)} proxies")
        
        working_proxies = []
        for proxy in self.proxies[:10]:
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
        
        if working_proxies:
            return random.choice(working_proxies)
        else:
            self.update_status("No working proxies found, continuing without proxy")
            return None
    
    def setup_driver(self):
        """Setup Chrome driver dengan konfigurasi"""
        chrome_options = Options()
        
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        proxy = self.get_working_proxy()
        if proxy:
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
            self.update_status(f"Using proxy: {proxy}")
        
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.update_status(f"Error setting up driver: {str(e)}")
            return None
    
    def update_status(self, message):
        """Update status dan kirim ke UI"""
        self.current_status = message
        timestamp = time.strftime("%H:%M:%S")
        socketio.emit('status_update', {
            'message': f"[{timestamp}] {message}",
            'cycle': self.current_cycle,
            'total_cycles': self.total_cycles
        })
        print(f"[{timestamp}] {message}")
    
    def check_ip_leak(self, driver):
        """Cek kebocoran IP"""
        try:
            driver.get("https://api.ipify.org")
            ip_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            current_ip = ip_element.text
            self.update_status(f"IP Check: {current_ip}")
            return True
        except Exception as e:
            self.update_status(f"IP leak check failed: {str(e)}")
            return False
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia"""
        try:
            self.update_status("Opening Google Search")
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            self.update_status(f"Searching for: {keyword}")
            
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            search_box.submit()
            time.sleep(random.uniform(3, 5))
            
            self.update_status(f"Looking for: {target_website}")
            target_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            
            if target_links:
                target_link = target_links[0]
                target_link.click()
                self.update_status("Clicked target website")
                time.sleep(random.uniform(3, 5))
                
                self.update_status("Scrolling to bottom")
                self.slow_scroll(driver)
                
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                links = driver.find_elements(By.TAG_NAME, "a")
                article_links = [link for link in links if self.is_article_link(link)]
                
                if article_links:
                    random_article = random.choice(article_links)
                    try:
                        random_article.click()
                        self.update_status("Clicked random article")
                        time.sleep(random.uniform(3, 5))
                        
                        self.update_status("Scrolling article for 20 seconds")
                        self.scroll_for_duration(driver, 20)
                        
                    except Exception as e:
                        self.update_status(f"Could not click article: {str(e)}")
                
                return True
            else:
                self.update_status("Target website not found in search results")
                return False
                
        except Exception as e:
            self.update_status(f"Simulation error: {str(e)}")
            return False
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        while current_position < total_height:
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Kadang berhenti sebentar
            if random.random() < 0.2:
                time.sleep(random.uniform(1, 3))
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-100, -50, 50, 100, 150])
            driver.execute_script(f"window.scrollBy(0, {scroll_direction});")
            time.sleep(random.uniform(0.5, 2))
    
    def is_article_link(self, link):
        """Cek jika link kemungkinan adalah artikel"""
        href = link.get_attribute('href')
        text = link.text.strip()
        
        if not href or not text:
            return False
        
        article_indicators = ['blog', 'article', 'post', 'news', '2023', '2024', 'read', 'story']
        href_lower = href.lower()
        text_lower = text.lower()
        
        return any(indicator in href_lower or indicator in text_lower for indicator in article_indicators)
    
    def clear_cache(self, driver):
        """Bersihkan cache dan cookies"""
        try:
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            driver.delete_all_cookies()
            self.update_status("Cache cleared")
        except Exception as e:
            self.update_status(f"Cache clear error: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles):
        """Jalankan semua cycles"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Starting cycle {self.current_cycle}/{cycles}")
            
            driver = self.setup_driver()
            if not driver:
                self.update_status("Failed to setup driver, skipping cycle")
                continue
            
            try:
                if not self.check_ip_leak(driver):
                    self.update_status("IP leak detected, skipping cycle")
                    continue
                
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} completed successfully")
                else:
                    self.update_status(f"Cycle {self.current_cycle} completed with issues")
                
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} failed: {str(e)}")
            finally:
                driver.quit()
            
            if cycle < cycles - 1 and self.is_running:
                self.update_status(f"Waiting {delay_between_cycles} seconds before next cycle")
                for i in range(delay_between_cycles):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        self.is_running = False
        self.update_status("All cycles completed!")

# Global instance
booster = SEOTrafficBooster()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Connected to SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Please provide keywords and target website!'})
        return
    
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster started successfully!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'SEO Booster stopping...'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)           
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        ]
        
        for api_url in api_sources:
            try:
                headers = {'User-Agent': self.ua.random}
                response = requests.get(api_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Parse response text untuk mendapatkan proxy
                    lines = response.text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line and not line.startswith('#'):
                            # Validasi format IP:PORT
                            parts = line.split(':')
                            if len(parts) == 2 and parts[1].isdigit():
                                all_proxies.append(line)
                                
                    self.update_status(f"Got {len(lines)} proxies from {api_url}")
                    
            except Exception as e:
                self.update_status(f"Error from {api_url}: {str(e)}")
                continue
        
        # Jika tidak ada proxy yang didapat, gunakan fallback
        if not all_proxies:
            all_proxies = self.get_fallback_proxies()
        
        return list(set(all_proxies))[:50]

    def get_fallback_proxies(self):
        """Fallback proxy list jika API tidak bekerja"""
        common_proxies = [
            "34.82.224.175:3128", 
            "35.185.196.38:3128", 
            "104.154.143.77:3128",
            "35.224.246.249:3128", 
            "34.83.225.238:3128"
        ]
        return common_proxies
    
    def test_proxy(self, proxy):
        """Test jika proxy berfungsi"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def get_working_proxy(self):
        """Dapatkan proxy yang berfungsi"""
        if not self.proxies:
            self.proxies = self.get_auto_proxies()
            self.update_status(f"Found {len(self.proxies)} proxies")
        
        working_proxies = []
        for proxy in self.proxies[:10]:
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
        
        if working_proxies:
            return random.choice(working_proxies)
        else:
            self.update_status("No working proxies found, continuing without proxy")
            return None
    
    def setup_driver(self):
        """Setup Chrome driver dengan konfigurasi"""
        chrome_options = Options()
        
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        proxy = self.get_working_proxy()
        if proxy:
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
            self.update_status(f"Using proxy: {proxy}")
        
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.update_status(f"Error setting up driver: {str(e)}")
            return None
    
    def update_status(self, message):
        """Update status dan kirim ke UI"""
        self.current_status = message
        timestamp = time.strftime("%H:%M:%S")
        socketio.emit('status_update', {
            'message': f"[{timestamp}] {message}",
            'cycle': self.current_cycle,
            'total_cycles': self.total_cycles
        })
        print(f"[{timestamp}] {message}")
    
    def check_ip_leak(self, driver):
        """Cek kebocoran IP"""
        try:
            driver.get("https://api.ipify.org")
            ip_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            current_ip = ip_element.text
            self.update_status(f"IP Check: {current_ip}")
            return True
        except Exception as e:
            self.update_status(f"IP leak check failed: {str(e)}")
            return False
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia"""
        try:
            self.update_status("Opening Google Search")
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            self.update_status(f"Searching for: {keyword}")
            
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            search_box.submit()
            time.sleep(random.uniform(3, 5))
            
            self.update_status(f"Looking for: {target_website}")
            target_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            
            if target_links:
                target_link = target_links[0]
                target_link.click()
                self.update_status("Clicked target website")
                time.sleep(random.uniform(3, 5))
                
                self.update_status("Scrolling to bottom")
                self.slow_scroll(driver)
                
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                links = driver.find_elements(By.TAG_NAME, "a")
                article_links = [link for link in links if self.is_article_link(link)]
                
                if article_links:
                    random_article = random.choice(article_links)
                    try:
                        random_article.click()
                        self.update_status("Clicked random article")
                        time.sleep(random.uniform(3, 5))
                        
                        self.update_status("Scrolling article for 20 seconds")
                        self.scroll_for_duration(driver, 20)
                        
                    except Exception as e:
                        self.update_status(f"Could not click article: {str(e)}")
                
                return True
            else:
                self.update_status("Target website not found in search results")
                return False
                
        except Exception as e:
            self.update_status(f"Simulation error: {str(e)}")
            return False
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        while current_position < total_height:
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Kadang berhenti sebentar
            if random.random() < 0.2:
                time.sleep(random.uniform(1, 3))
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-100, -50, 50, 100, 150])
            driver.execute_script(f"window.scrollBy(0, {scroll_direction});")
            time.sleep(random.uniform(0.5, 2))
    
    def is_article_link(self, link):
        """Cek jika link kemungkinan adalah artikel"""
        href = link.get_attribute('href')
        text = link.text.strip()
        
        if not href or not text:
            return False
        
        article_indicators = ['blog', 'article', 'post', 'news', '2023', '2024', 'read', 'story']
        href_lower = href.lower()
        text_lower = text.lower()
        
        return any(indicator in href_lower or indicator in text_lower for indicator in article_indicators)
    
    def clear_cache(self, driver):
        """Bersihkan cache dan cookies"""
        try:
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            driver.delete_all_cookies()
            self.update_status("Cache cleared")
        except Exception as e:
            self.update_status(f"Cache clear error: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles):
        """Jalankan semua cycles"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Starting cycle {self.current_cycle}/{cycles}")
            
            driver = self.setup_driver()
            if not driver:
                self.update_status("Failed to setup driver, skipping cycle")
                continue
            
            try:
                if not self.check_ip_leak(driver):
                    self.update_status("IP leak detected, skipping cycle")
                    continue
                
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} completed successfully")
                else:
                    self.update_status(f"Cycle {self.current_cycle} completed with issues")
                
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} failed: {str(e)}")
            finally:
                driver.quit()
            
            if cycle < cycles - 1 and self.is_running:
                self.update_status(f"Waiting {delay_between_cycles} seconds before next cycle")
                for i in range(delay_between_cycles):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        self.is_running = False
        self.update_status("All cycles completed!")

# Global instance
booster = SEOTrafficBooster()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Connected to SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Please provide keywords and target website!'})
        return
    
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster started successfully!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'SEO Booster stopping...'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=US',
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        ]
        
        for api_url in api_sources:
            try:
                headers = {'User-Agent': self.ua.random}
                response = requests.get(api_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Parse response text untuk mendapatkan proxy
                    lines = response.text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line and not line.startswith('#'):
                            # Validasi format IP:PORT
                            parts = line.split(':')
                            if len(parts) == 2 and parts[1].isdigit():
                                all_proxies.append(line)
                                
                    self.update_status(f"Got {len(lines)} proxies from {api_url}")
                    
            except Exception as e:
                self.update_status(f"Error from {api_url}: {str(e)}")
                continue
        
        # Jika tidak ada proxy yang didapat, gunakan fallback
        if not all_proxies:
            all_proxies = self.get_fallback_proxies()
        
        return list(set(all_proxies))[:50]

    def get_fallback_proxies(self):
        """Fallback proxy list jika API tidak bekerja"""
        common_proxies = [
            "34.82.224.175:3128", 
            "35.185.196.38:3128", 
            "104.154.143.77:3128",
            "35.224.246.249:3128", 
            "34.83.225.238:3128"
        ]
        return common_proxies
    
    def test_proxy(self, proxy):
        """Test jika proxy berfungsi"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def get_working_proxy(self):
        """Dapatkan proxy yang berfungsi"""
        if not self.proxies:
            self.proxies = self.get_auto_proxies()
            self.update_status(f"Found {len(self.proxies)} proxies")
        
        working_proxies = []
        for proxy in self.proxies[:10]:
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
        
        if working_proxies:
            return random.choice(working_proxies)
        else:
            self.update_status("No working proxies found, continuing without proxy")
            return None
    
    def setup_driver(self):
        """Setup Chrome driver dengan konfigurasi"""
        chrome_options = Options()
        
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        proxy = self.get_working_proxy()
        if proxy:
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
            self.update_status(f"Using proxy: {proxy}")
        
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.update_status(f"Error setting up driver: {str(e)}")
            return None
    
    def update_status(self, message):
        """Update status dan kirim ke UI"""
        self.current_status = message
        timestamp = time.strftime("%H:%M:%S")
        socketio.emit('status_update', {
            'message': f"[{timestamp}] {message}",
            'cycle': self.current_cycle,
            'total_cycles': self.total_cycles
        })
        print(f"[{timestamp}] {message}")
    
    def check_ip_leak(self, driver):
        """Cek kebocoran IP"""
        try:
            driver.get("https://api.ipify.org")
            ip_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            current_ip = ip_element.text
            self.update_status(f"IP Check: {current_ip}")
            return True
        except Exception as e:
            self.update_status(f"IP leak check failed: {str(e)}")
            return False
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia"""
        try:
            self.update_status("Opening Google Search")
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            self.update_status(f"Searching for: {keyword}")
            
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            search_box.submit()
            time.sleep(random.uniform(3, 5))
            
            self.update_status(f"Looking for: {target_website}")
            target_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            
            if target_links:
                target_link = target_links[0]
                target_link.click()
                self.update_status("Clicked target website")
                time.sleep(random.uniform(3, 5))
                
                self.update_status("Scrolling to bottom")
                self.slow_scroll(driver)
                
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                links = driver.find_elements(By.TAG_NAME, "a")
                article_links = [link for link in links if self.is_article_link(link)]
                
                if article_links:
                    random_article = random.choice(article_links)
                    try:
                        random_article.click()
                        self.update_status("Clicked random article")
                        time.sleep(random.uniform(3, 5))
                        
                        self.update_status("Scrolling article for 20 seconds")
                        self.scroll_for_duration(driver, 20)
                        
                    except Exception as e:
                        self.update_status(f"Could not click article: {str(e)}")
                
                return True
            else:
                self.update_status("Target website not found in search results")
                return False
                
        except Exception as e:
            self.update_status(f"Simulation error: {str(e)}")
            return False
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        while current_position < total_height:
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Kadang berhenti sebentar
            if random.random() < 0.2:
                time.sleep(random.uniform(1, 3))
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-100, -50, 50, 100, 150])
            driver.execute_script(f"window.scrollBy(0, {scroll_direction});")
            time.sleep(random.uniform(0.5, 2))
    
    def is_article_link(self, link):
        """Cek jika link kemungkinan adalah artikel"""
        href = link.get_attribute('href')
        text = link.text.strip()
        
        if not href or not text:
            return False
        
        article_indicators = ['blog', 'article', 'post', 'news', '2023', '2024', 'read', 'story']
        href_lower = href.lower()
        text_lower = text.lower()
        
        return any(indicator in href_lower or indicator in text_lower for indicator in article_indicators)
    
    def clear_cache(self, driver):
        """Bersihkan cache dan cookies"""
        try:
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            driver.delete_all_cookies()
            self.update_status("Cache cleared")
        except Exception as e:
            self.update_status(f"Cache clear error: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles):
        """Jalankan semua cycles"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Starting cycle {self.current_cycle}/{cycles}")
            
            driver = self.setup_driver()
            if not driver:
                self.update_status("Failed to setup driver, skipping cycle")
                continue
            
            try:
                if not self.check_ip_leak(driver):
                    self.update_status("IP leak detected, skipping cycle")
                    continue
                
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} completed successfully")
                else:
                    self.update_status(f"Cycle {self.current_cycle} completed with issues")
                
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} failed: {str(e)}")
            finally:
                driver.quit()
            
            if cycle < cycles - 1 and self.is_running:
                self.update_status(f"Waiting {delay_between_cycles} seconds before next cycle")
                for i in range(delay_between_cycles):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        self.is_running = False
        self.update_status("All cycles completed!")

# Global instance
booster = SEOTrafficBooster()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Connected to SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Please provide keywords and target website!'})
        return
    
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster started successfully!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'SEO Booster stopping...'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=US',
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        ]
        
        for api_url in api_sources:
            try:
                headers = {'User-Agent': self.ua.random}
                response = requests.get(api_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Parse response text untuk mendapatkan proxy
                    lines = response.text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line and not line.startswith('#'):
                            # Validasi format IP:PORT
                            parts = line.split(':')
                            if len(parts) == 2 and parts[1].isdigit():
                                all_proxies.append(line)
                                
                    self.update_status(f"Got {len(lines)} proxies from {api_url}")
                    
            except Exception as e:
                self.update_status(f"Error from {api_url}: {str(e)}")
                continue
        
        # Jika tidak ada proxy yang didapat, gunakan fallback
        if not all_proxies:
            all_proxies = self.get_fallback_proxies()
        
        return list(set(all_proxies))[:50]

    def get_fallback_proxies(self):
        """Fallback proxy list jika API tidak bekerja"""
        common_proxies = [
            "34.82.224.175:3128", 
            "35.185.196.38:3128", 
            "104.154.143.77:3128",
            "35.224.246.249:3128", 
            "34.83.225.238:3128"
        ]
        return common_proxies
    
    def test_proxy(self, proxy):
        """Test jika proxy berfungsi"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def get_working_proxy(self):
        """Dapatkan proxy yang berfungsi"""
        if not self.proxies:
            self.proxies = self.get_auto_proxies()
            self.update_status(f"Found {len(self.proxies)} proxies")
        
        working_proxies = []
        for proxy in self.proxies[:10]:
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
        
        if working_proxies:
            return random.choice(working_proxies)
        else:
            self.update_status("No working proxies found, continuing without proxy")
            return None
    
    def setup_driver(self):
        """Setup Chrome driver dengan konfigurasi"""
        chrome_options = Options()
        
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        proxy = self.get_working_proxy()
        if proxy:
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
            self.update_status(f"Using proxy: {proxy}")
        
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.update_status(f"Error setting up driver: {str(e)}")
            return None
    
    def update_status(self, message):
        """Update status dan kirim ke UI"""
        self.current_status = message
        timestamp = time.strftime("%H:%M:%S")
        socketio.emit('status_update', {
            'message': f"[{timestamp}] {message}",
            'cycle': self.current_cycle,
            'total_cycles': self.total_cycles
        })
        print(f"[{timestamp}] {message}")
    
    def check_ip_leak(self, driver):
        """Cek kebocoran IP"""
        try:
            driver.get("https://api.ipify.org")
            ip_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            current_ip = ip_element.text
            self.update_status(f"IP Check: {current_ip}")
            return True
        except Exception as e:
            self.update_status(f"IP leak check failed: {str(e)}")
            return False
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia"""
        try:
            self.update_status("Opening Google Search")
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            self.update_status(f"Searching for: {keyword}")
            
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            search_box.submit()
            time.sleep(random.uniform(3, 5))
            
            self.update_status(f"Looking for: {target_website}")
            target_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            
            if target_links:
                target_link = target_links[0]
                target_link.click()
                self.update_status("Clicked target website")
                time.sleep(random.uniform(3, 5))
                
                self.update_status("Scrolling to bottom")
                self.slow_scroll(driver)
                
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                links = driver.find_elements(By.TAG_NAME, "a")
                article_links = [link for link in links if self.is_article_link(link)]
                
                if article_links:
                    random_article = random.choice(article_links)
                    try:
                        random_article.click()
                        self.update_status("Clicked random article")
                        time.sleep(random.uniform(3, 5))
                        
                        self.update_status("Scrolling article for 20 seconds")
                        self.scroll_for_duration(driver, 20)
                        
                    except Exception as e:
                        self.update_status(f"Could not click article: {str(e)}")
                
                return True
            else:
                self.update_status("Target website not found in search results")
                return False
                
        except Exception as e:
            self.update_status(f"Simulation error: {str(e)}")
            return False
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        while current_position < total_height:
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.5))
            
            if random.random() < 0.2:
                time.sleep(random.uniform(1, 3))
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-100, -50, 50, 100, 150])
            driver.execute_script(f"window.scrollBy(0, {scroll_direction});")
            time.sleep(random.uniform(0.5, 2))
    
    def is_article_link(self, link):
        """Cek jika link kemungkinan adalah artikel"""
        href = link.get_attribute('href')
        text = link.text.strip()
        
        if not href or not text:
            return False
        
        article_indicators = ['blog', 'article', 'post', 'news', '2023', '2024', 'read', 'story']
        href_lower = href.lower()
        text_lower = text.lower()
        
        return any(indicator in href_lower or indicator in text_lower for indicator in article_indicators)
    
    def clear_cache(self, driver):
        """Bersihkan cache dan cookies"""
        try:
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            driver.delete_all_cookies()
            self.update_status("Cache cleared")
        except Exception as e:
            self.update_status(f"Cache clear error: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles):
        """Jalankan semua cycles"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Starting cycle {self.current_cycle}/{cycles}")
            
            driver = self.setup_driver()
            if not driver:
                self.update_status("Failed to setup driver, skipping cycle")
                continue
            
            try:
                if not self.check_ip_leak(driver):
                    self.update_status("IP leak detected, skipping cycle")
                    continue
                
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} completed successfully")
                else:
                    self.update_status(f"Cycle {self.current_cycle} completed with issues")
                
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} failed: {str(e)}")
            finally:
                driver.quit()
            
            if cycle < cycles - 1 and self.is_running:
                self.update_status(f"Waiting {delay_between_cycles} seconds before next cycle")
                for i in range(delay_between_cycles):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        self.is_running = False
        self.update_status("All cycles completed!")

booster = SEOTrafficBooster()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Connected to SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Please provide keywords and target website!'})
        return
    
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster started successfully!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'SEO Booster stopping...'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)       
            # Kadang berhenti sebentar
            if random.random() < 0.2:
                time.sleep(random.uniform(1, 3))
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-100, -50, 50, 100, 150])
            driver.execute_script(f"window.scrollBy(0, {scroll_direction});")
            time.sleep(random.uniform(0.5, 2))
    
    def is_article_link(self, link):
        """Cek jika link kemungkinan adalah artikel"""
        href = link.get_attribute('href')
        text = link.text.strip()
        
        if not href or not text:
            return False
        
        # Filter link yang kemungkinan adalah artikel
        article_indicators = ['blog', 'article', 'post', 'news', '2023', '2024', 'read', 'story']
        href_lower = href.lower()
        text_lower = text.lower()
        
        return any(indicator in href_lower or indicator in text_lower for indicator in article_indicators)
    
    def clear_cache(self, driver):
        """Bersihkan cache dan cookies"""
        try:
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            driver.delete_all_cookies()
            self.update_status("Cache cleared")
        except Exception as e:
            self.update_status(f"Cache clear error: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles):
        """Jalankan semua cycles"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Starting cycle {self.current_cycle}/{cycles}")
            
            driver = self.setup_driver()
            if not driver:
                self.update_status("Failed to setup driver, skipping cycle")
                continue
            
            try:
                # Cek IP leak
                if not self.check_ip_leak(driver):
                    self.update_status("IP leak detected, skipping cycle")
                    continue
                
                # Jalankan simulasi
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} completed successfully")
                else:
                    self.update_status(f"Cycle {self.current_cycle} completed with issues")
                
                # Bersihkan cache
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} failed: {str(e)}")
            finally:
                driver.quit()
            
            # Delay antara cycles jika bukan cycle terakhir
            if cycle < cycles - 1 and self.is_running:
                self.update_status(f"Waiting {delay_between_cycles} seconds before next cycle")
                for i in range(delay_between_cycles):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        self.is_running = False
        self.update_status("All cycles completed!")

# Global instance
booster = SEOTrafficBooster()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Connected to SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Please provide keywords and target website!'})
        return
    
    # Jalankan di thread terpisah
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster started successfully!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'SEO Booster stopping...'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=US',
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        ]
        
        for api_url in api_sources:
            try:
                headers = {'User-Agent': self.ua.random}
                response = requests.get(api_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Parse response text untuk mendapatkan proxy
                    lines = response.text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line and not line.startswith('#'):
                            # Validasi format IP:PORT
                            parts = line.split(':')
                            if len(parts) == 2 and parts[1].isdigit():
                                all_proxies.append(line)
                                
                    self.update_status(f"Got {len(lines)} proxies from {api_url}")
                    
            except Exception as e:
                self.update_status(f"Error from {api_url}: {str(e)}")
                continue
        
        # Jika tidak ada proxy yang didapat, gunakan fallback
        if not all_proxies:
            all_proxies = self.get_fallback_proxies()
        
        return list(set(all_proxies))[:50]  # Batasi hingga 50 proxy

    def get_fallback_proxies(self):
        """Fallback proxy list jika API tidak bekerja"""
        # Beberapa public proxy (harus di-test)
        common_proxies = [
            "34.82.224.175:3128", "35.185.196.38:3128", "104.154.143.77:3128",
            "35.224.246.249:3128", "34.83.225.238:3128"
        ]
        
        return common_proxies
    
    def test_proxy(self, proxy):
        """Test jika proxy berfungsi"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def get_working_proxy(self):
        """Dapatkan proxy yang berfungsi"""
        if not self.proxies:
            self.proxies = self.get_auto_proxies()
            self.update_status(f"Found {len(self.proxies)} proxies")
        
        # Test dan pilih proxy yang berfungsi
        working_proxies = []
        for proxy in self.proxies[:10]:  # Test 10 proxy pertama
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
        
        if working_proxies:
            return random.choice(working_proxies)
        else:
            self.update_status("No working proxies found, continuing without proxy")
            return None
    
    def setup_driver(self):
        """Setup Chrome driver dengan konfigurasi"""
        chrome_options = Options()
        
        # Random User Agent
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        # Proxy settings
        proxy = self.get_working_proxy()
        if proxy:
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
            self.update_status(f"Using proxy: {proxy}")
        
        # Additional options untuk menghindari deteksi
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.update_status(f"Error setting up driver: {str(e)}")
            return None
    
    def update_status(self, message):
        """Update status dan kirim ke UI"""
        self.current_status = message
        timestamp = time.strftime("%H:%M:%S")
        socketio.emit('status_update', {
            'message': f"[{timestamp}] {message}",
            'cycle': self.current_cycle,
            'total_cycles': self.total_cycles
        })
        print(f"[{timestamp}] {message}")
    
    def check_ip_leak(self, driver):
        """Cek kebocoran IP"""
        try:
            driver.get("https://api.ipify.org")
            ip_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            current_ip = ip_element.text
            self.update_status(f"IP Check: {current_ip}")
            return True
        except Exception as e:
            self.update_status(f"IP leak check failed: {str(e)}")
            return False
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia"""
        try:
            # Step 1: Google Search
            self.update_status("Opening Google Search")
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            # Step 2: Input keyword
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            self.update_status(f"Searching for: {keyword}")
            
            # Ketik seperti manusia
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            search_box.submit()
            time.sleep(random.uniform(3, 5))
            
            # Step 3: Cari dan klik website target
            self.update_status(f"Looking for: {target_website}")
            target_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            
            if target_links:
                target_link = target_links[0]
                target_link.click()
                self.update_status("Clicked target website")
                time.sleep(random.uniform(3, 5))
                
                # Step 4: Scroll pelan ke bawah
                self.update_status("Scrolling to bottom")
                self.slow_scroll(driver)
                
                # Step 5: Kembali ke atas
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                # Step 6: Cari dan klik postingan acak
                links = driver.find_elements(By.TAG_NAME, "a")
                article_links = [link for link in links if self.is_article_link(link)]
                
                if article_links:
                    random_article = random.choice(article_links)
                    try:
                        random_article.click()
                        self.update_status("Clicked random article")
                        time.sleep(random.uniform(3, 5))
                        
                        # Step 7: Scroll selama 20 detik
                        self.update_status("Scrolling article for 20 seconds")
                        self.scroll_for_duration(driver, 20)
                        
                    except Exception as e:
                        self.update_status(f"Could not click article: {str(e)}")
                
                return True
            else:
                self.update_status("Target website not found in search results")
                return False
                
        except Exception as e:
            self.update_status(f"Simulation error: {str(e)}")
            return False
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        current_position = 0
        while current_position < total_height:
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Kadang berhenti sebentar
            if random.random() < 0.2:
                time.sleep(random.uniform(1, 3))
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-100, -50, 50, 100, 150])
            driver.execute_script(f"window.scrollBy(0, {scroll_direction});")
            time.sleep(random.uniform(0.5, 2))
    
    def is_article_link(self, link):
        """Cek jika link kemungkinan adalah artikel"""
        href = link.get_attribute('href')
        text = link.text.strip()
        
        if not href or not text:
            return False
        
        # Filter link yang kemungkinan adalah artikel
        article_indicators = ['blog', 'article', 'post', 'news', '2023', '2024', 'read', 'story']
        href_lower = href.lower()
        text_lower = text.lower()
        
        return any(indicator in href_lower or indicator in text_lower for indicator in article_indicators)
    
    def clear_cache(self, driver):
        """Bersihkan cache dan cookies"""
        try:
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            driver.delete_all_cookies()
            self.update_status("Cache cleared")
        except Exception as e:
            self.update_status(f"Cache clear error: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles):
        """Jalankan semua cycles"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Starting cycle {self.current_cycle}/{cycles}")
            
            driver = self.setup_driver()
            if not driver:
                self.update_status("Failed to setup driver, skipping cycle")
                continue
            
            try:
                # Cek IP leak
                if not self.check_ip_leak(driver):
                    self.update_status("IP leak detected, skipping cycle")
                    continue
                
                # Jalankan simulasi
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} completed successfully")
                else:
                    self.update_status(f"Cycle {self.current_cycle} completed with issues")
                
                # Bersihkan cache
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} failed: {str(e)}")
            finally:
                driver.quit()
            
            # Delay antara cycles jika bukan cycle terakhir
            if cycle < cycles - 1 and self.is_running:
                self.update_status(f"Waiting {delay_between_cycles} seconds before next cycle")
                for i in range(delay_between_cycles):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        self.is_running = False
        self.update_status("All cycles completed!")

# Global instance
booster = SEOTrafficBooster()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Connected to SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Please provide keywords and target website!'})
        return
    
    # Jalankan di thread terpisah
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster started successfully!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'SEO Booster stopping...'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)        'https://www.proxy-list.download/api/v1/get?type=http'
    ]
    
    all_proxies = []
    
    for source in proxy_sources:
        try:
            headers = {'User-Agent': self.ua.random}
            response = requests.get(source, headers=headers, timeout=10)
            
            if 'free-proxy-list' in source or 'sslproxies' in source or 'us-proxy' in source:
                # Gunakan html5lib parser sebagai alternatif
                soup = BeautifulSoup(response.text, 'html.parser')
                # Cari tabel dengan cara yang lebih sederhana
                if 'proxylisttable' in response.text:
                    # Ekstrak IP dan port dengan regex
                    import re
                    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                    port_pattern = r'<td>(\d{2,5})</td>'
                    
                    ips = re.findall(ip_pattern, response.text)
                    ports = re.findall(port_pattern, response.text)
                    
                    for ip, port in zip(ips[:20], ports[:20]):
                        all_proxies.append(f"{ip}:{port}")
            
            elif 'proxy-list.download' in source:
                proxies = response.text.strip().split('\n')
                all_proxies.extend([p.strip() for p in proxies if p.strip()][:20])
                
        except Exception as e:
            self.update_status(f"Error getting proxies from {source}: {str(e)}")
            continue
    
    return list(set(all_proxies))
    
    def test_proxy(self, proxy):
        """Test jika proxy berfungsi"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def get_working_proxy(self):
        """Dapatkan proxy yang berfungsi"""
        if not self.proxies:
            self.proxies = self.get_auto_proxies()
            self.update_status(f"Found {len(self.proxies)} proxies")
        
        # Test dan pilih proxy yang berfungsi
        working_proxies = []
        for proxy in self.proxies[:10]:  # Test 10 proxy pertama
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
        
        if working_proxies:
            return random.choice(working_proxies)
        else:
            self.update_status("No working proxies found, continuing without proxy")
            return None
    
    def setup_driver(self):
        """Setup Chrome driver dengan konfigurasi"""
        chrome_options = Options()
        
        # Random User Agent
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        # Proxy settings
        proxy = self.get_working_proxy()
        if proxy:
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
            self.update_status(f"Using proxy: {proxy}")
        
        # Additional options untuk menghindari deteksi
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.update_status(f"Error setting up driver: {str(e)}")
            return None
    
    def update_status(self, message):
        """Update status dan kirim ke UI"""
        self.current_status = message
        timestamp = time.strftime("%H:%M:%S")
        socketio.emit('status_update', {
            'message': f"[{timestamp}] {message}",
            'cycle': self.current_cycle,
            'total_cycles': self.total_cycles
        })
        print(f"[{timestamp}] {message}")
    
    def check_ip_leak(self, driver):
        """Cek kebocoran IP"""
        try:
            driver.get("https://api.ipify.org")
            ip_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            current_ip = ip_element.text
            self.update_status(f"IP Check: {current_ip}")
            return True
        except Exception as e:
            self.update_status(f"IP leak check failed: {str(e)}")
            return False
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia"""
        try:
            # Step 1: Google Search
            self.update_status("Opening Google Search")
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            # Step 2: Input keyword
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            self.update_status(f"Searching for: {keyword}")
            
            # Ketik seperti manusia
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            search_box.submit()
            time.sleep(random.uniform(3, 5))
            
            # Step 3: Cari dan klik website target
            self.update_status(f"Looking for: {target_website}")
            target_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            
            if target_links:
                target_link = target_links[0]
                target_link.click()
                self.update_status("Clicked target website")
                time.sleep(random.uniform(3, 5))
                
                # Step 4: Scroll pelan ke bawah
                self.update_status("Scrolling to bottom")
                self.slow_scroll(driver)
                
                # Step 5: Kembali ke atas
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                # Step 6: Cari dan klik postingan acak
                links = driver.find_elements(By.TAG_NAME, "a")
                article_links = [link for link in links if self.is_article_link(link)]
                
                if article_links:
                    random_article = random.choice(article_links)
                    try:
                        random_article.click()
                        self.update_status("Clicked random article")
                        time.sleep(random.uniform(3, 5))
                        
                        # Step 7: Scroll selama 20 detik
                        self.update_status("Scrolling article for 20 seconds")
                        self.scroll_for_duration(driver, 20)
                        
                    except Exception as e:
                        self.update_status(f"Could not click article: {str(e)}")
                
                return True
            else:
                self.update_status("Target website not found in search results")
                return False
                
        except Exception as e:
            self.update_status(f"Simulation error: {str(e)}")
            return False
    
    def slow_scroll(self, driver):
        """Scroll pelan seperti manusia"""
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        current_position = 0
        while current_position < total_height:
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Kadang berhenti sebentar
            if random.random() < 0.2:
                time.sleep(random.uniform(1, 3))
    
    def scroll_for_duration(self, driver, seconds):
        """Scroll untuk durasi tertentu"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            scroll_direction = random.choice([-100, -50, 50, 100, 150])
            driver.execute_script(f"window.scrollBy(0, {scroll_direction});")
            time.sleep(random.uniform(0.5, 2))
    
    def is_article_link(self, link):
        """Cek jika link kemungkinan adalah artikel"""
        href = link.get_attribute('href')
        text = link.text.strip()
        
        if not href or not text:
            return False
        
        # Filter link yang kemungkinan adalah artikel
        article_indicators = ['blog', 'article', 'post', 'news', '2023', '2024', 'read', 'story']
        href_lower = href.lower()
        text_lower = text.lower()
        
        return any(indicator in href_lower or indicator in text_lower for indicator in article_indicators)
    
    def clear_cache(self, driver):
        """Bersihkan cache dan cookies"""
        try:
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            driver.delete_all_cookies()
            self.update_status("Cache cleared")
        except Exception as e:
            self.update_status(f"Cache clear error: {str(e)}")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles):
        """Jalankan semua cycles"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"Starting cycle {self.current_cycle}/{cycles}")
            
            driver = self.setup_driver()
            if not driver:
                self.update_status("Failed to setup driver, skipping cycle")
                continue
            
            try:
                # Cek IP leak
                if not self.check_ip_leak(driver):
                    self.update_status("IP leak detected, skipping cycle")
                    continue
                
                # Jalankan simulasi
                keyword = random.choice(keywords)
                success = self.simulate_human_behavior(driver, keyword, target_website)
                
                if success:
                    self.update_status(f"Cycle {self.current_cycle} completed successfully")
                else:
                    self.update_status(f"Cycle {self.current_cycle} completed with issues")
                
                # Bersihkan cache
                self.clear_cache(driver)
                
            except Exception as e:
                self.update_status(f"Cycle {self.current_cycle} failed: {str(e)}")
            finally:
                driver.quit()
            
            # Delay antara cycles jika bukan cycle terakhir
            if cycle < cycles - 1 and self.is_running:
                self.update_status(f"Waiting {delay_between_cycles} seconds before next cycle")
                for i in range(delay_between_cycles):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        self.is_running = False
        self.update_status("All cycles completed!")

# Global instance
booster = SEOTrafficBooster()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Connected to SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Please provide keywords and target website!'})
        return
    
    # Jalankan di thread terpisah
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster started successfully!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'SEO Booster stopping...'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
