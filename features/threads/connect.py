import time
import os
from utils.driver_utils import create_driver
from config import config

def connect_threads(uid, cookies, proxy_str=None, ua_str=None):
    """
    Khởi tạo trình duyệt, nạp cookie Instagram và điều hướng sang Threads.
    Returns:
        bool: True nếu login thành công, False nếu thất bại (cookie chết).
    """
    #print(f"\n🚀 Đang xử lý tài khoản: {uid}")

    user_data_dir = None
    if uid:
        user_data_dir = os.path.join(os.getcwd(), "profiles", uid)
        #print(f"📁 Profile: {user_data_dir}")
        
    proxy_config = None
    proxy_type = getattr(config, 'PROXY_TYPE', 0)
    
    if proxy_type != 0 and proxy_str:
        proxy_parts = proxy_str.split(":")
        if len(proxy_parts) == 5:
            proxy_config = {
                "host": proxy_parts[0].strip(),
                "port": proxy_parts[1].strip(),
                "user": proxy_parts[3].strip(),
                "pass": proxy_parts[4].strip()
            }
        elif len(proxy_parts) >= 4:
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
        driver, wait, proxy_config = create_driver(user_data_dir=user_data_dir, proxy_config=proxy_config, user_agent=ua_str)
        
        if proxy_config:
            print(f"✅ Proxy: {proxy_config.get('host')}:{proxy_config.get('port')}")
        else:
            print("⚠️ Dùng IP trực tiếp.")

        
        print("🌍 Mở Instagram để kiểm tra phiên đăng nhập...")
        driver.get("https://www.instagram.com/")
        time.sleep(3)
        
        # Kiểm tra xem profile đã có sẵn cookie đăng nhập chưa (sessionid)
        is_logged_in = False
        if driver.get_cookie("sessionid") or "login" not in driver.current_url.lower():
            # Có thể đã đăng nhập, thử lấy cookie sessionid để chắc chắn
            if driver.get_cookie("sessionid"):
                is_logged_in = True
                print("⚡ Profile đã lưu phiên đăng nhập, bỏ qua bước nạp Cookie mới!")
                
                # Vẫn phải kiểm tra nếu cookie còn sống nhưng bị suspended
                if "accounts/suspended" in driver.current_url.lower():
                    print("[ACCOUNT_DIE]")
                    #print("❌ Tài khoản đã bị đình chỉ (Suspended)!")
                    return "die"
        
        login_method = getattr(config, 'LOGIN_METHOD', 0)

        if not is_logged_in:
            cookie_failed = False
            if login_method == 0 and cookies:
                print(f"🔄 Đang ưu tiên đăng nhập bằng Cookie. Đang nạp {len(cookies)} cookies mới...")
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except Exception:
                        pass
                
                print("♻️ Làm mới trang Instagram...")
                driver.refresh()
                time.sleep(5)
                
                current_url = driver.current_url.lower()
                if "accounts/suspended" in current_url:
                    print("[ACCOUNT_DIE]")
                    print("❌ Tài khoản đã bị đình chỉ (Suspended)!")
                    return "die"
                    
                if "login" in current_url or not driver.get_cookie("sessionid") or driver.find_elements(By.NAME, "pass") or driver.find_elements(By.NAME, "password"):
                    print("❌ Cookie đã chết hoặc không hợp lệ. Đang chuyển sang đăng nhập bằng Password...")
                    cookie_failed = True
                else:
                    print("✅ Đăng nhập Instagram bằng Cookie thành công!")

            if login_method == 1 or cookie_failed or (login_method == 0 and not cookies):
                if login_method == 1:
                    print("🔄 Bắt đầu tiến trình đăng nhập bằng Username / Password...")
                elif not cookies:
                    print("❌ Không có cookie để đăng nhập. Đang thử đăng nhập bằng Password...")

                password = ""
                two_fa_secret = ""
                try:
                    with open("resources/account.txt", "r", encoding="utf-8") as f:
                        for line in f:
                            parts = line.strip().split("|")
                            if parts and parts[0] == uid:
                                password = parts[1] if len(parts) > 1 else ""
                                two_fa_secret = parts[2] if len(parts) > 2 else "" 
                                break
                except:
                    pass
                    
                if not password:
                    print("❌ Không có mật khẩu để đăng nhập fallback.")
                    return False

                try:
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support import expected_conditions as EC
                    import random

                    def human_typing_local(element, text):
                        for char in text:
                            element.send_keys(char)
                            time.sleep(random.uniform(0.05, 0.25))

                    def check_account_suspended_local(url):
                        if "accounts/suspended" in url or "/suspended/" in url:
                            print("💀 TÀI KHOẢN ĐÃ DIE (Suspended)!")
                            return True
                        return False

                    email_inputs = driver.find_elements(By.NAME, "username")
                    if not email_inputs:
                        email_inputs = driver.find_elements(By.NAME, "email")
                    email_input = next((el for el in email_inputs if el.is_displayed()), None)
                    if not email_input:
                        email_input = wait.until(EC.element_to_be_clickable((By.NAME, "username")))

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_input)
                    time.sleep(1)
                    email_input.click()
                    email_input.clear()
                    print("⏳ Đang nhập Username...")
                    human_typing_local(email_input, uid)

                    pass_inputs = driver.find_elements(By.NAME, "password")
                    if not pass_inputs:
                        pass_inputs = driver.find_elements(By.NAME, "pass")
                    pass_input = next((el for el in pass_inputs if el.is_displayed()), None)
                    if not pass_input:
                        pass_input = wait.until(EC.element_to_be_clickable((By.NAME, "password")))

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pass_input)
                    time.sleep(1)
                    pass_input.click()
                    pass_input.clear()
                    print("⏳ Đang nhập Password...")
                    human_typing_local(pass_input, password)

                    time.sleep(1)
                    login_btn_xpath = "//button[@type='submit'] | //div[@role='button' and (contains(., 'Log in') or contains(., 'Log In') or contains(., 'Đăng nhập'))]"
                    login_btn = driver.find_element(By.XPATH, login_btn_xpath)
                    driver.execute_script("arguments[0].click();", login_btn)
                    print("✅ Đã click nút Log in!")

                    # Kiểm tra trạng thái
                    print("⏳ Đang kiểm tra kết quả đăng nhập...")
                    error_xpath = "//span[contains(text(), 'The password you entered is incorrect') or contains(., 'Sai mật khẩu')]"
                    blocked_xpath = "//span[contains(text(), 'The login information you entered is incorrect')]"
                    
                    login_success = False
                    two_fa_needed = False

                    for _ in range(60):
                        try:
                            curl = driver.current_url
                            if check_account_suspended_local(curl):
                                return "die"
                            
                            if any(msg.is_displayed() for msg in driver.find_elements(By.XPATH, error_xpath)):
                                print("❌ LỖI: Sai mật khẩu!")
                                return False
                                
                            if any(msg.is_displayed() for msg in driver.find_elements(By.XPATH, blocked_xpath)):
                                print("🚫 LỖI: Bị chặn đăng nhập!")
                                return False

                            if "two_step_verification" in curl or "two_factor_login" in curl:
                                print("🔐 Phát hiện 2FA!")
                                two_fa_needed = True
                                break

                            if "accounts/onetap" in curl:
                                print("✅ Phát hiện trang lưu thông tin đăng nhập (onetap)!")
                                try:
                                    save_info_btn = driver.find_element(By.XPATH, "//button[@type='button' and (contains(., 'Save info') or contains(., 'Lưu thông tin'))]")
                                    driver.execute_script("arguments[0].click();", save_info_btn)
                                    print("✅ Đã click Lưu thông tin!")
                                    time.sleep(5)
                                except: pass
                                login_success = True
                                break
                            
                            if curl.strip('/') == "https://www.instagram.com":
                                # Chỉ đánh giá là thành công nếu tìm thấy thẻ SVG Home (chứng tỏ đã qua được màn login)
                                if driver.find_elements(By.XPATH, "//svg[@aria-label='Home' or @aria-label='Trang chủ']"):
                                    print("🎉 ĐĂNG NHẬP THÀNH CÔNG (Vào thẳng trang chủ)!")
                                    login_success = True
                                    break
                        except: pass
                        time.sleep(1)

                    if two_fa_needed and two_fa_secret:
                        print("⏳ Đang đợi ô nhập mã 2FA xuất hiện...")
                        time.sleep(5) # Đợi React render form 2FA
                        try:
                            code_inputs = driver.find_elements(By.XPATH, "//input[@name='verificationCode' or @autocomplete='off' or @type='tel']")
                            code_input = next((el for el in code_inputs if el.is_displayed()), None)
                            if not code_input:
                                code_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='verificationCode' or @autocomplete='off' or @type='tel']")))

                            import pyotp
                            totp = pyotp.TOTP(two_fa_secret)
                            code = totp.now()
                            print(f"🔑 Nhập mã 2FA: {code}")
                            
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", code_input)
                            time.sleep(1)
                            code_input.click()
                            code_input.clear()
                            human_typing_local(code_input, code)
                            
                            time.sleep(random.uniform(1.0, 2.0))
                            
                            continue_btn_xpath = "//div[@role='button' and (contains(., 'Continue') or contains(., 'Tiếp tục'))] | //button[contains(., 'Continue') or contains(., 'Tiếp tục')]"
                            continue_btn = driver.find_element(By.XPATH, continue_btn_xpath)
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_btn)
                            time.sleep(random.uniform(0.5, 1.5))
                            driver.execute_script("arguments[0].click();", continue_btn)
                            print("✅ Đã click nút Continue!")
                            
                            for _ in range(30):
                                curl = driver.current_url
                                if check_account_suspended_local(curl):
                                    return "die"
                                    
                                if "accounts/onetap" in curl:
                                    print("✅ Phát hiện trang lưu thông tin đăng nhập (onetap)!")
                                    login_success = True
                                    break
                                elif curl.strip('/') == "https://www.instagram.com" and driver.find_elements(By.XPATH, "//svg[@aria-label='Home' or @aria-label='Trang chủ']"):
                                    print("🎉 ĐĂNG NHẬP THÀNH CÔNG (Vào thẳng trang chủ)!")
                                    login_success = True
                                    break
                                time.sleep(1)

                        except Exception as e:
                            print(f"⚠️ Lỗi xử lý 2FA: {e}")
                            return False

                    if not login_success:
                        print("❌ Đăng nhập bằng Password thất bại.")
                        return False
                        
                    print("✅ Đăng nhập bằng Password thành công!")
                except Exception as e:
                    print(f"❌ Lỗi khi đăng nhập bằng Password: {e}")
                    return False
        
        print("🌐 Đang chuyển hướng sang trang Threads...")
        driver.get("https://www.threads.net/")

        try:
            print("⏳ Đợi hộp thoại 'Join with Instagram' xuất hiện...")
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            
            # Dùng XPath tối giản: tìm thẻ div đóng vai trò button, bên trong có chứa icon Instagram
            xpath = "//div[@role='button' and .//i[@aria-label='Instagram']]"
            
            # Đợi phần tử có mặt trong DOM (không dùng clickable vì đôi khi thẻ div bị thẻ span che khuất)
            login_btn = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            print("👆 Đã tìm thấy nút đăng nhập, đang tiến hành click...")
            
            # Dùng Javascript click để ép click xuyên qua các lớp phủ (overlays) hoặc element bị che
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", login_btn)
            
            time.sleep(5)
            print("✅ Đã bấm đăng nhập Threads bằng Instagram thành công!")

            # Kiểm tra modal thiết lập Public/Private profile (Nút Next)
            try:
                print("⏳ Kiểm tra modal Public/Private profile (Nút Next)...")
                # Tìm div có role=button và chứa chữ Next
                next_xpath = "//div[@role='button' and contains(translate(., 'NEXT', 'next'), 'next')]"
                next_btns = driver.find_elements(By.XPATH, next_xpath)
                if next_btns:
                    print("👆 Đã tìm thấy nút Next, đang thử click...")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btns[0])
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", next_btns[0])
                    time.sleep(3)
                else:
                    print("Không thấy modal Next, bỏ qua.")
            except Exception as e:
                print(f"⚠️ Lỗi khi xử lý modal Next: {e}")

            # Kiểm tra modal Powered by Instagram (Nút Join Threads)
            try:
                print("⏳ Kiểm tra modal Powered by Instagram (Nút Join Threads)...")
                # Tìm div có role=button và chứa chữ Join
                join_xpath = "//div[@role='button' and contains(translate(., 'JOIN', 'join'), 'join')]"
                join_btns = driver.find_elements(By.XPATH, join_xpath)
                if join_btns:
                    print("👆 Đã tìm thấy nút Join, đang thử click...")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", join_btns[0])
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", join_btns[0])
                    
                    import random
                    wait_join = random.randint(10, 15)
                    print(f"⏳ Đợi {wait_join}s sau khi nhấn Join...")
                    time.sleep(wait_join)
                else:
                    print("Không thấy modal Join, bỏ qua.")
            except Exception as e:
                print(f"⚠️ Lỗi khi xử lý modal Join: {e}")

        except Exception as e:
            print(f"⚠️ Không tìm thấy nút đăng nhập Threads tự động hoặc có lỗi: {e}")

        # Kiểm tra tài khoản có bị đình chỉ không
        current_url = driver.current_url.lower()
        if "accounts/suspended" in current_url:
            print("[ACCOUNT_DIE]")
            print("❌ Tài khoản đã bị đình chỉ (Suspended) sau khi vào Threads!")
            return "die"

        # Kiểm tra trạng thái đăng nhập thành công qua nút Compose/Đăng bài
        print("⏳ Đang chờ tải giao diện trang chủ Threads (kiểm tra nút Đăng bài)...")
        xpath1 = "//div[@role='button' and @aria-label='Empty text field. Type to compose a new post.']"
        xpath2 = "//div[@role='button' and .//svg[@aria-label='Create']]"
        
        login_success = False
        for _ in range(60): # Thử tối đa 60 lần (60 giây)
            try:
                # Dùng find_elements để không bị throw Exception nếu không tìm thấy ngay
                if driver.find_elements(By.XPATH, xpath1) or driver.find_elements(By.XPATH, xpath2):
                    login_success = True
                    break
            except:
                pass
            time.sleep(1)

        if not login_success:
            print("❌ Quá 60s nhưng không tải được nút Đăng bài. Có thể đăng nhập bị lỗi hoặc mạng chậm!")
            return False
            
        print("✅ Đã tải thành công giao diện trang chủ Threads, sẵn sàng hoạt động!")

        import random
        wait_time = random.randint(1, 10)
        print(f"🎉 Hoàn tất kết nối Threads. Tự động chuyển sang tài khoản tiếp theo sau {wait_time} giây...")
        time.sleep(wait_time)
                
        return True
            
    except Exception as e:
        print(f"❌ Lỗi khi xử lý tài khoản {uid}: {e}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def open_chrome_only(uid, proxy_str=None, ua_str=None):
    """
    Chỉ mở trình duyệt Chrome với profile, không thực hiện tác vụ nào cả.
    """
    user_data_dir = None
    if uid:
        user_data_dir = os.path.join(os.getcwd(), "profiles", uid)
        
    proxy_config = None
    proxy_type = getattr(config, 'PROXY_TYPE', 0)
    
    if proxy_type != 0 and proxy_str:
        proxy_parts = proxy_str.split(":")
        if len(proxy_parts) == 5:
            proxy_config = {
                "host": proxy_parts[0].strip(),
                "port": proxy_parts[1].strip(),
                "user": proxy_parts[3].strip(),
                "pass": proxy_parts[4].strip()
            }
        elif len(proxy_parts) >= 4:
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

    try:
        driver, wait, proxy_config = create_driver(user_data_dir=user_data_dir, proxy_config=proxy_config, user_agent=ua_str)
        
        print("[CHROME_READY]")
        
        # Giữ script chạy để không bị đóng Chrome
        while True:
            try:
                _ = driver.window_handles
                time.sleep(1)
            except Exception:
                break
                
    except Exception as e:
        print("[CHROME_ERROR]")
        pass
