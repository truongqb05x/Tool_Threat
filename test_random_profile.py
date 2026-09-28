import os
import random
import time
from utils.driver_utils import create_driver
from utils.account_utils import read_all_accounts_data
from config import config

def test_random_profile():
    print("🧪 Bắt đầu chạy test mở Chrome với một Profile ngẫu nhiên...")
    
    print("\n👉 Chọn chế độ:")
    print("  1 - Lướt newfeed (thả tym ngẫu nhiên)")
    print("  2 - Đọc thông báo")
    mode_input = input("Nhập lựa chọn [Mặc định: 1]: ").strip()
    try:
        mode = int(mode_input)
    except:
        mode = 1
        
    if mode == 1:
        minutes_input = input("\n👉 Nhập số phút lướt newfeed [Mặc định: 1]: ").strip()
        try:
            scroll_minutes = int(minutes_input)
            if scroll_minutes <= 0: scroll_minutes = 1
        except:
            scroll_minutes = 1
    elif mode == 2:
        scroll_minutes = 0
    else:
        scroll_minutes = 1


    profiles_dir = os.path.join(os.getcwd(), "profiles")
    
    # Kiểm tra xem thư mục profiles có tồn tại không
    if not os.path.exists(profiles_dir):
        print("⚠️ Thư mục 'profiles' chưa tồn tại. Vui lòng chạy tính năng 1 trước để tạo profile.")
        return
        
    # Lấy danh sách các thư mục con trong profiles (chính là các UID)
    available_profiles = [d for d in os.listdir(profiles_dir) if os.path.isdir(os.path.join(profiles_dir, d))]
    
    if not available_profiles:
        print("⚠️ Không có Profile nào bên trong thư mục 'profiles'.")
        return
        
    # Chọn ngẫu nhiên 1 UID
    random_uid = random.choice(available_profiles)
    user_data_dir = os.path.join(profiles_dir, random_uid)
    
    print(f"🎲 Đã chọn ngẫu nhiên Profile: {random_uid}")
    print(f"📁 Đường dẫn Profile: {user_data_dir}")
    
    # Lấy proxy và user_agent từ file account.txt
    accounts = read_all_accounts_data()
    proxy_str = None
    ua_str = None
    account_index = -1
    if accounts:
        for idx, (u, cookies, p_str, ua) in enumerate(accounts):
            if u == random_uid:
                proxy_str = p_str
                ua_str = ua
                account_index = idx
                break
                
    proxy_config = None
    proxy_type = getattr(config, 'PROXY_TYPE', 0)
    
    if proxy_type != 0 and proxy_str:
        proxy_parts = proxy_str.split(":")
        if len(proxy_parts) >= 4:
            proxy_config = {
                "host": proxy_parts[0].strip(),
                "port": proxy_parts[1].strip(),
                "user": proxy_parts[2].strip(),
                "pass": proxy_parts[3].strip()
            }
        elif len(proxy_parts) >= 2:
            proxy_config = {
                "host": proxy_parts[0].strip(),
                "port": proxy_parts[1].strip(),
                "user": "",
                "pass": ""
            }
    elif proxy_type == 0:
        print("⚠️ Cấu hình đang chọn 'Không dùng Proxy'.")
    
    driver = None
    try:
        # Mở Chrome với profile ngẫu nhiên, gắn proxy và user_agent
        driver, wait, proxy_config = create_driver(user_data_dir=user_data_dir, proxy_config=proxy_config, user_agent=ua_str)

        
        if proxy_config:
            print(f"✅ Đã cấu hình proxy: {proxy_config.get('host')}:{proxy_config.get('port')}")
        else:
            print("⚠️ Không có proxy nào được cấu hình, đang dùng IP trực tiếp.")
            
        print("🌐 Đang tải trang chủ Threads...")
        driver.get("https://www.threads.net/")
        time.sleep(random.uniform(4, 7))

        if mode == 1:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            
            print(f"⏳ Bắt đầu lướt newfeed trong {scroll_minutes} phút...")
            start_time = time.time()
            end_time = start_time + (scroll_minutes * 60)
            
            while time.time() < end_time:
                # Cuộn trang ngẫu nhiên
                scroll_amount = random.randint(400, 1000)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(2, 5))
                
                # Xác suất 30% sẽ thả tym khi đang lướt
                if random.random() < 0.3:
                    try:
                        # Tìm các nút like (Thích hoặc Like)
                        like_xpath = "//div[@role='button' and .//*[local-name()='svg' and (@title='Thích' or @title='Like')]]"
                        like_btns = driver.find_elements(By.XPATH, like_xpath)
                        
                        visible_btns = []
                        for btn in like_btns:
                            if btn.is_displayed():
                                visible_btns.append(btn)
                                
                        if visible_btns:
                            btn_to_click = random.choice(visible_btns)
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_to_click)
                            time.sleep(1.5)
                            
                            try:
                                btn_to_click.click()
                            except:
                                try:
                                    from selenium.webdriver.common.action_chains import ActionChains
                                    ActionChains(driver).move_to_element(btn_to_click).click().perform()
                                except:
                                    driver.execute_script("arguments[0].click();", btn_to_click)
                                    
                            # Kiểm tra xem có thực sự đã tym chưa (title chuyển thành Bỏ thích / Unlike)
                            time.sleep(1.5)
                            try:
                                svg = btn_to_click.find_element(By.XPATH, ".//*[local-name()='svg']")
                                title = svg.get_attribute("title")
                                if title and title.strip() in ['Bỏ thích', 'Unlike']:
                                    print("❤️ Đã thả tym thành công!")
                                else:
                                    print("⚠️ Đã thử click tym nhưng có vẻ chưa ăn (title hiện tại: " + str(title) + ")")
                            except:
                                print("❤️ Đã click tym (nhưng không thể xác minh trạng thái)!")
                    except Exception as e:
                        pass
                        
            print(f"✅ Đã hoàn thành lướt newfeed trong {scroll_minutes} phút!")

        elif mode == 2:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            
            wait_time = random.uniform(5, 10)
            print(f"⏳ Đang chờ {wait_time:.1f}s trước khi vào đọc thông báo...")
            time.sleep(wait_time)
            
            print("🌐 Đang truy cập https://www.threads.net/activity...")
            driver.get("https://www.threads.net/activity")
            
            time.sleep(random.uniform(3, 6))
            
            print("🔍 Đang tìm các thông báo...")
            try:
                # Tìm các div chứa thông báo
                notify_xpath = "//div[starts-with(@data-pagelet, 'threads_activity_feed_')]//div[@data-pressable-container='true']"
                notifications = driver.find_elements(By.XPATH, notify_xpath)
                
                if not notifications:
                    notify_xpath = "//div[starts-with(@data-pagelet, 'threads_activity_feed_')]//a[@role='link']"
                    notifications = driver.find_elements(By.XPATH, notify_xpath)
                
                if notifications:
                    visible_notifs = [n for n in notifications if n.is_displayed()]
                    if visible_notifs:
                        notif_to_click = random.choice(visible_notifs)
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", notif_to_click)
                        time.sleep(1.5)
                        print("🖱️ Đang nhấn ngẫu nhiên vào 1 thông báo...")
                        
                        try:
                            notif_to_click.click()
                        except:
                            try:
                                from selenium.webdriver.common.action_chains import ActionChains
                                ActionChains(driver).move_to_element(notif_to_click).click().perform()
                            except:
                                driver.execute_script("arguments[0].click();", notif_to_click)
                                
                        print("✅ Đã nhấn đọc thông báo!")
                    else:
                        print("⚠️ Không có thông báo nào đang hiển thị trên màn hình.")
                else:
                    print("⚠️ Không tìm thấy thông báo nào.")
            except Exception as e:
                print(f"❌ Lỗi khi đọc thông báo: {e}")

        print("🎉 Hoàn tất. Vui lòng đóng trình duyệt bằng tay để kết thúc test...")
        # Treo trình duyệt đợi user đóng
        while True:
            try:
                _ = driver.window_handles
                time.sleep(2)
            except Exception:
                print("👋 Đã nhận diện trình duyệt đóng, kết thúc test.")
                break
                
    except Exception as e:
        print(f"❌ Lỗi khi test mở trình duyệt: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    test_random_profile()
