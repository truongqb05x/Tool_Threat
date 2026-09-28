import sys
import os
import random
import time

# Cấu hình đường dẫn project để import được utils và config
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.driver_utils import create_driver
from config import config

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def human_typing(element, text):
    """Giả lập gõ phím từ từ như người thật"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.25))


def check_account_suspended(current_url):
    """Kiểm tra xem tài khoản có bị suspended/die dựa trên URL không"""
    if "accounts/suspended" in current_url or "/suspended/" in current_url:
        print("💀 TÀI KHOẢN ĐÃ DIE (Suspended)!")
        print(f"   URL hiện tại: {current_url}")
        return True
    return False


def open_ig_demo():
    """
    Mở Chrome cho 1 tài khoản ngẫu nhiên, truy cập Instagram
    Tuân thủ logic proxy và tạo profile giống trong connect.py
    """
    uid = "JohnyJames14112"
    username = "JohnyJames14112"
    password = "HEOihBOe6331"

    proxy_str = "miennam.vnproxy.com:41773:8K35Fz:4jIe50"
    ua_str = None

    print(f"\n🚀 Đang mở tài khoản Demo: {uid}")

    user_data_dir = os.path.join(project_root, "profiles", uid)
    print(f"📁 Đường dẫn Profile: {user_data_dir}")

    proxy_config = None
    # Forcing proxy_type = 1 để đảm bảo demo luôn chạy qua proxy (bỏ qua config.py)
    proxy_type = 1

    # Logic xử lý proxy chuẩn theo connect.py
    if proxy_type != 0 and proxy_str:
        proxy_parts = proxy_str.split(":")
        if len(proxy_parts) == 5:
            # Format: host:port:ip:user:pass -> bỏ qua IP (index 2)
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
        print("⚠️ Cấu hình hiện tại là 'Không dùng Proxy'.")

    driver = None
    try:
        # Khởi tạo trình duyệt
        driver, wait, applied_proxy = create_driver(
            user_data_dir=user_data_dir,
            proxy_config=proxy_config,
            user_agent=ua_str
        )

        if applied_proxy:
            print(f"✅ Đang dùng Proxy: {applied_proxy.get('host')}:{applied_proxy.get('port')}")
        else:
            print("⚠️ Truy cập bằng IP thật của máy.")

        print("🌍 Đang truy cập trang chủ Instagram...")
        driver.get("https://www.instagram.com/")

        print("⏳ Đợi tải trang và tìm ô nhập tài khoản...")
        time.sleep(4)  # Chờ animation/overlay của trang web tải xong

        # Điền Username: Tìm ô name="email" đang hiển thị
        email_inputs = driver.find_elements(By.NAME, "email")
        email_input = next((el for el in email_inputs if el.is_displayed()), None)
        if not email_input:
            email_input = wait.until(EC.element_to_be_clickable((By.NAME, "email")))

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_input)
        time.sleep(random.uniform(0.5, 1.5))
        email_input.click()  # Focus vào ô nhập
        email_input.clear()

        print("⏳ Đang nhập Username...")
        human_typing(email_input, username)
        print("✅ Đã điền username.")

        time.sleep(random.uniform(0.5, 1.5))

        # Điền Password: Tương tự
        pass_inputs = driver.find_elements(By.NAME, "pass")
        pass_input = next((el for el in pass_inputs if el.is_displayed()), None)
        if not pass_input:
            pass_input = wait.until(EC.element_to_be_clickable((By.NAME, "pass")))

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pass_input)
        time.sleep(random.uniform(0.5, 1.5))
        pass_input.click()
        pass_input.clear()

        print("⏳ Đang nhập Password...")
        human_typing(pass_input, password)
        print("✅ Đã điền password.")

        time.sleep(random.uniform(1.0, 2.0))

        # Click nút Log in
        login_btn_xpath = "//div[@role='button' and (contains(., 'Log in') or contains(., 'Log In') or @aria-label='Log In' or contains(., 'Đăng nhập'))]"
        login_btn = driver.find_element(By.XPATH, login_btn_xpath)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_btn)
        time.sleep(random.uniform(0.5, 1.5))
        driver.execute_script("arguments[0].click();", login_btn)
        print("✅ Đã click nút Log in!")

        print("⏳ Đang kiểm tra trạng thái đăng nhập (tối đa 60s)...")
        error_xpath = "//span[contains(text(), 'The password you entered is incorrect') or contains(., 'Sai mật khẩu')]"
        blocked_xpath = "//span[contains(text(), 'The login information you entered is incorrect')]"
        login_failed = False
        login_blocked = False
        two_fa_needed = False
        account_suspended = False  # Cờ đánh dấu tài khoản bị die
        login_success = False

        for _ in range(60):
            try:
                current_url = driver.current_url

                # === KIỂM TRA TÀI KHOẢN BỊ SUSPENDED / DIE ===
                if check_account_suspended(current_url):
                    account_suspended = True
                    break

                # Kiểm tra báo sai mật khẩu
                error_msgs = driver.find_elements(By.XPATH, error_xpath)
                if any(msg.is_displayed() for msg in error_msgs):
                    print("❌ LỖI: Thông tin đăng nhập sai (Incorrect Password)!")
                    login_failed = True
                    break

                # Kiểm tra bị chặn đăng nhập
                blocked_msgs = driver.find_elements(By.XPATH, blocked_xpath)
                if any(msg.is_displayed() for msg in blocked_msgs):
                    print("🚫 LỖI: Bị chặn đăng nhập (Login Blocked)!")
                    login_blocked = True
                    break

                # Kiểm tra chuyển sang trang 2FA
                if "two_step_verification" in current_url or "two_factor_login" in current_url:
                    print("🔐 Phát hiện trang xác thực 2 bước (2FA)!")
                    two_fa_needed = True
                    break

                # === KIỂM TRA ĐĂNG NHẬP THÀNH CÔNG ===
                if "accounts/onetap" in current_url:
                    print("✅ Phát hiện trang lưu thông tin đăng nhập (onetap)!")
                    try:
                        save_info_btn = driver.find_element(By.XPATH, "//button[@type='button' and (contains(., 'Save info') or contains(., 'Lưu thông tin'))]")
                        driver.execute_script("arguments[0].click();", save_info_btn)
                        print("✅ Đã click Lưu thông tin!")
                        time.sleep(5)
                    except:
                        pass
                    print("🎉 ĐĂNG NHẬP THÀNH CÔNG!")
                    login_success = True
                    break
                
                # Kiểm tra vào thẳng trang chủ
                if current_url.strip('/') == "https://www.instagram.com":
                    # Đảm bảo không còn ô nhập password (tức là đã qua form đăng nhập)
                    if not driver.find_elements(By.NAME, "pass"):
                        print("🎉 ĐĂNG NHẬP THÀNH CÔNG (Vào thẳng trang chủ)!")
                        login_success = True
                        break

            except:
                pass
            time.sleep(1)

        # === NẾU TÀI KHOẢN DIE THÌ DỪNG LUÔN, KHÔNG XỬ LÝ 2FA ===
        if account_suspended:
            print("\n🚫 Tài khoản đã bị suspended, kết thúc kiểm tra.")
            input("\n>>> NHẤN ENTER Ở ĐÂY ĐỂ KẾT THÚC VÀ ĐÓNG TRÌNH DUYỆT <<<\n")
            return

        if login_blocked:
            print("\n🚫 Tài khoản đã bị chặn đăng nhập, kết thúc kiểm tra.")
            input("\n>>> NHẤN ENTER Ở ĐÂY ĐỂ KẾT THÚC VÀ ĐÓNG TRÌNH DUYỆT <<<\n")
            return

        # Xử lý 2FA
        if two_fa_needed:
            print("⏳ Đang đợi ô nhập mã 2FA xuất hiện...")
            # Tìm ô nhập mã 2FA (id="_r_3_" hoặc type="text" có autocomplete="off")
            try:
                code_inputs = driver.find_elements(By.CSS_SELECTOR, "input[autocomplete='off'][type='text']")
                code_input = next((el for el in code_inputs if el.is_displayed()), None)
                if not code_input:
                    code_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[autocomplete='off'][type='text']")))

                print("✅ Đã thấy ô nhập mã 2FA, tiến hành lấy mã...")
                import pyotp
                two_fa_secret = "4FRWGMADQYW7PWIISEAMNC7UXPDIZG2I"
                totp = pyotp.TOTP(two_fa_secret)
                code = totp.now()
                print(f"🔑 Mã 2FA hiện tại: {code}")

                time.sleep(random.uniform(1.0, 2.0))

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", code_input)
                time.sleep(random.uniform(0.5, 1.0))
                code_input.click()
                code_input.clear()

                print("⏳ Đang nhập mã 2FA từng chữ...")
                human_typing(code_input, code)
                print(f"✅ Đã nhập mã 2FA: {code}")

                time.sleep(random.uniform(1.0, 2.0))

                # Click nút Continue
                continue_btn_xpath = "//div[@role='button' and (contains(., 'Continue') or contains(., 'Tiếp tục'))]"
                continue_btn = driver.find_element(By.XPATH, continue_btn_xpath)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_btn)
                time.sleep(random.uniform(0.5, 1.5))
                driver.execute_script("arguments[0].click();", continue_btn)
                print("✅ Đã click nút Continue!")

            except Exception as e2fa:
                print(f"⚠️ Lỗi khi xử lý 2FA: {e2fa}")

        if not login_failed:
            print("\n🎉 Vui lòng xem tiến trình đăng nhập trên trình duyệt.")

        # Chờ user nhập enter để kết thúc
        input("\n>>> NHẤN ENTER Ở ĐÂY ĐỂ KẾT THÚC CHƯƠNG TRÌNH VÀ ĐÓNG TRÌNH DUYỆT <<<\n")

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")
        input("\n>>> NHẤN ENTER Ở ĐÂY ĐỂ ĐÓNG TRÌNH DUYỆT (Lỗi) <<<\n")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


if __name__ == "__main__":
    open_ig_demo()