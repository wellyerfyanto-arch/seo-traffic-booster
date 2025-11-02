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
import eventlet # Dipertahankan untuk penggunaan threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seo_traffic_booster_secret'
# PERBAIKAN KRITIS: Menghapus async_mode='eventlet' agar autodeteksi berhasil
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
            # Menggunakan undetected-chromedriver atau memastikan chromedriver di PATH
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
    
    def simulate_human_behavior(self, driver, keyword, target_website):
        """Simulasi perilaku manusia"""
        try:
            self.update_status("Membuka Google Search")
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
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
            
            self.update_status(f"Mencari: {target_website}")
            target_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            
            if target_links:
                target_link = target_links[0]
                target_link.click()
                self.update_status("Berhasil klik website target")
                time.sleep(random.uniform(3, 5))
                
                self.update_status("Scrolling ke bawah")
                self.slow_scroll(driver)
                
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
                
                # Coba klik link internal acak
                links = driver.find_elements(By.TAG_NAME, "a")
                if links:
                    try:
                        random_link = random.choice(links)
                        random_link.click()
                        self.update_status("Klik artikel random")
                        time.sleep(random.uniform(3, 5))
                        
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
    
    if not keywords or not target_website:
        emit('error', {'message': 'Masukkan keywords dan website target!'})
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
    # Pastikan Anda menjalankan ini di lingkungan yang mendukung Flask-SocketIO
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
