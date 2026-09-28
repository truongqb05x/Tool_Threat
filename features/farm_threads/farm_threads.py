import time
import os
import random
from utils.driver_utils import create_driver, calculate_window_pos, extract_and_send_threads_cookie
from config import config
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

class ThreadFarmer:
    def __init__(self, driver, uid, cookie_threads, is_scroll, is_like, like_delay_min, like_delay_max, is_read_notif, notif_count):
        self.driver = driver
        self.uid = uid
        self.cookie_threads = cookie_threads
        self.is_scroll = is_scroll
        self.is_like = is_like
        self.like_delay_min = like_delay_min
        self.like_delay_max = like_delay_max
        self.is_read_notif = is_read_notif
        self.notif_count = notif_count
        
        self.notifs_read = 0

    def go_to_home(self):
        print(f"[{self.uid}] 🌐 Đang tải trang chủ Threads...")
        self.driver.get("https://www.threads.net/")
        time.sleep(random.uniform(4, 7))
        extract_and_send_threads_cookie(self.driver, self.uid, self.cookie_threads)

    def scroll_and_like(self, duration_mins):
        if duration_mins <= 0:
            return
            
        print(f"[{self.uid}] ⏳ Lướt newfeed trong {duration_mins:.1f} phút...")
        start_time = time.time()
        end_time = start_time + (duration_mins * 60)
        
        next_like_time = time.time() + random.uniform(self.like_delay_min, self.like_delay_max) if self.is_like else float('inf')
        next_reload_time = time.time() + random.uniform(90, 120)
        
        while time.time() < end_time:
            if time.time() >= next_reload_time:
                print(f"[{self.uid}] 🔄 Đang tải lại trang...")
                self.driver.refresh()
                time.sleep(random.uniform(4, 7))
                next_reload_time = time.time() + random.uniform(60, 90)
                continue
                
            scroll_amount = random.randint(400, 1000)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(2, 5))
            
            if self.is_like and time.time() >= next_like_time:
                self._like_post()
                next_like_time = time.time() + random.uniform(self.like_delay_min, self.like_delay_max)

    def _like_post(self):
        try:
            like_xpath = "//div[@role='button' and .//*[local-name()='svg' and (@title='Thích' or @title='Like')]]"
            like_btns = self.driver.find_elements(By.XPATH, like_xpath)
            
            visible_btns = [btn for btn in like_btns if btn.is_displayed()]
            if visible_btns:
                btn_to_click = random.choice(visible_btns)
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_to_click)
                time.sleep(1.5)
                
                try:
                    btn_to_click.click()
                except:
                    try:
                        ActionChains(self.driver).move_to_element(btn_to_click).click().perform()
                    except:
                        self.driver.execute_script("arguments[0].click();", btn_to_click)
                        
                time.sleep(1.5)
                try:
                    svg = btn_to_click.find_element(By.XPATH, ".//*[local-name()='svg']")
                    title = svg.get_attribute("title")
                    if title and title.strip() in ['Bỏ thích', 'Unlike']:
                        print(f"[{self.uid}] ❤️ Đã thả tym thành công!")
                    else:
                        print(f"[{self.uid}] ⚠️ Đã click tym nhưng không thể xác minh (title: {title})")
                except:
                    print(f"[{self.uid}] ❤️ Đã click tym (không thể xác minh)!")
        except Exception as e:
            pass

    def read_notifications(self, count):
        if count <= 0:
            return
            
        print(f"[{self.uid}] 🌐 Đang truy cập thông báo...")
        self.driver.get("https://www.threads.net/activity")
        time.sleep(random.uniform(3, 6))
        
        print(f"[{self.uid}] 🔍 Cần đọc {count} thông báo.")
        for i in range(count):
            try:
                notify_xpath = "//div[starts-with(@data-pagelet, 'threads_activity_feed_')]//div[@data-pressable-container='true']"
                notifications = self.driver.find_elements(By.XPATH, notify_xpath)
                
                if not notifications:
                    notify_xpath = "//div[starts-with(@data-pagelet, 'threads_activity_feed_')]//a[@role='link']"
                    notifications = self.driver.find_elements(By.XPATH, notify_xpath)
                
                if notifications:
                    visible_notifs = [n for n in notifications if n.is_displayed()]
                    if visible_notifs:
                        notif_to_click = random.choice(visible_notifs)
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", notif_to_click)
                        time.sleep(1.5)
                        
                        print(f"[{self.uid}] 🖱️ Đang nhấn đọc thông báo thứ {i+1}...")
                        try:
                            notif_to_click.click()
                        except:
                            try:
                                ActionChains(self.driver).move_to_element(notif_to_click).click().perform()
                            except:
                                self.driver.execute_script("arguments[0].click();", notif_to_click)
                        
                        self.notifs_read += 1
                        time.sleep(random.uniform(3, 6))
                    else:
                        print(f"[{self.uid}] ⚠️ Không có thông báo hiển thị trên màn hình.")
                        break
                else:
                    print(f"[{self.uid}] ⚠️ Không tìm thấy thông báo nào.")
                    break
            except Exception as e:
                print(f"[{self.uid}] ❌ Lỗi khi đọc thông báo: {e}")
                break

    def run_nurture_flow(self, total_mins):
        print(f"\n🚀 Bắt đầu nuôi tài khoản {self.uid} trong tổng cộng {total_mins} phút")
        start_time = time.time()
        end_time = start_time + (total_mins * 60)
        
        if self.is_read_notif and self.notif_count > 0:
            self.read_notifications(self.notif_count)
            
        time_left_sec = end_time - time.time()
        if time_left_sec > 0 and self.is_scroll:
            self.go_to_home()
            self.scroll_and_like(time_left_sec / 60.0)
            
        time_left_sec = end_time - time.time()
        if time_left_sec > 0:
            print(f"[{self.uid}] ⏳ Chờ {time_left_sec:.1f}s cho đến khi hết thời gian nuôi...")
            time.sleep(time_left_sec)
                
        print(f"[{self.uid}] ✅ Hoàn tất quá trình nuôi tài khoản.")

def farm_threads(uid, cookies, proxy_str, ua_str, account_index, cookie_threads, is_scroll, is_like, like_delay_min, like_delay_max, is_read_notif, notif_count, total_mins):
    from features.threads.connect import connect_threads
    from utils.account_utils import update_account_status
    
    print(f"[{uid}] 🔍 Đang gọi connect_threads để kiểm tra đăng nhập/trạng thái tài khoản...")
    login_result = connect_threads(uid, cookies, proxy_str, ua_str)
    
    if login_result == "die":
        print(f"[{uid}] ❌ Tài khoản đã Die. Cập nhật trạng thái và dừng nuôi!")
        update_account_status(uid, "Die")
        return False
    elif not login_result:
        print(f"[{uid}] ❌ Đăng nhập thất bại. Dừng nuôi tài khoản!")
        return False

    user_data_dir = None
    if uid:
        user_data_dir = os.path.join(os.getcwd(), "profiles", uid)
        
    proxy_config = None
    proxy_type = getattr(config, 'PROXY_TYPE', 0)
    if proxy_type != 0 and proxy_str:
        proxy_parts = proxy_str.split(":")
        if len(proxy_parts) >= 4:
            proxy_config = {"host": proxy_parts[0].strip(), "port": proxy_parts[1].strip(), "user": proxy_parts[2].strip(), "pass": proxy_parts[3].strip()}
        elif len(proxy_parts) >= 2:
            proxy_config = {"host": proxy_parts[0].strip(), "port": proxy_parts[1].strip(), "user": "", "pass": ""}

    window_pos = calculate_window_pos(account_index)
    driver = None
    try:
        driver, wait, proxy_config = create_driver(user_data_dir=user_data_dir, proxy_config=proxy_config, user_agent=ua_str)
        if window_pos:
            driver.set_window_position(window_pos[0], window_pos[1])
            driver.set_window_size(window_pos[2], window_pos[3])
            
        farmer = ThreadFarmer(driver, uid, cookie_threads, is_scroll, is_like, like_delay_min, like_delay_max, is_read_notif, notif_count)
        farmer.run_nurture_flow(total_mins)
        
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ Lỗi chạy nuôi tài khoản cho UID {uid}: {str(e)}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

