import time
import os
import random
from utils.driver_utils import create_driver, calculate_window_pos, extract_and_send_threads_cookie
from config import config
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def post_to_threads(uid, cookies, proxy_str, ua_str, account_index, content_source="1", api_prompt="", hashtag_text="", media_paths=None, excel_path=""):
    """
    Thực hiện đăng bài lên Threads cho một tài khoản.
    Returns:
        bool: True nếu đăng thành công, False nếu thất bại.
    """
    from features.threads.connect import connect_threads
    from utils.account_utils import update_account_status
    
    print(f"\n🚀 Đang xử lý đăng bài cho tài khoản: {uid}")
    print(f"[{uid}] 🔍 Đang gọi connect_threads để kiểm tra đăng nhập/trạng thái tài khoản...")
    login_result = connect_threads(uid, cookies, proxy_str, ua_str)
    
    if login_result == "die":
        print(f"[{uid}] ❌ Tài khoản đã Die. Cập nhật trạng thái và dừng đăng bài!")
        update_account_status(uid, "Die")
        return False
    elif not login_result:
        print(f"[{uid}] ❌ Đăng nhập thất bại. Dừng đăng bài!")
        return False

    user_data_dir = None
    if uid:
        user_data_dir = os.path.join(os.getcwd(), "profiles", uid)
        
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

    driver = None
    try:
        window_pos = calculate_window_pos(account_index)
        driver, wait, proxy_config = create_driver(user_data_dir=user_data_dir, proxy_config=proxy_config, window_pos=window_pos, user_agent=ua_str)
        
        print("🌐 Mở thẳng Threads.net để tiến hành đăng bài...")
        driver.get("https://www.threads.net/")
        time.sleep(5)
        
        xpath1 = "//div[@role='button' and @aria-label='Empty text field. Type to compose a new post.']"
        xpath2 = "//div[@role='button' and .//svg[@aria-label='Create']]"
        
        compose_btn = None
        try:
            compose_btn = wait.until(EC.presence_of_element_located((By.XPATH, xpath1)))
        except:
            try:
                compose_btn = wait.until(EC.presence_of_element_located((By.XPATH, xpath2)))
            except:
                pass
                
        if not compose_btn:
            print("❌ Không tìm thấy nút đăng bài. Bỏ qua tài khoản này.")
            return False
            
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", compose_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", compose_btn)
        print("✅ Đã bấm mở modal Đăng bài thành công!")
        time.sleep(3)
        
        # Chuẩn bị nội dung
        stt_text = ""
        if content_source == "1":
            try:
                import pandas as pd
                data_path = excel_path if excel_path else os.path.join(os.getcwd(), "resources", "data.xlsx")
                if os.path.exists(data_path):
                    df = pd.read_excel(data_path)
                    if account_index != -1 and account_index < len(df):
                        stt_text = str(df.iloc[account_index]['CONTENT'])
                        print(f"📝 Đã lấy nội dung từ data.xlsx cho tài khoản thứ {account_index + 1}")
                    else:
                        print(f"⚠️ Tài khoản thứ {account_index + 1} vượt quá số dữ liệu trong data.xlsx")
                else:
                    print(f"⚠️ Không tìm thấy file {data_path}. Vui lòng tạo file có cột STT và CONTENT.")
            except ImportError:
                print("⚠️ Vui lòng mở Terminal và chạy lệnh: pip install pandas openpyxl")
            except Exception as e:
                print(f"⚠️ Lỗi đọc data.xlsx: {e}")
        elif content_source == "2":
            print("🔄 Đang gọi Gemini API để tạo nội dung...")
            try:
                from google import genai
                API_KEY = "YOUR_API_KEY_HERE"
                client = genai.Client(api_key=API_KEY)
                
                system_rule = "Bạn là một chuyên gia tạo content mạng xã hội Threads. Hãy viết nội dung ngắn gọn, súc tích (1-3 câu), có chứa emoji phù hợp. TRẢ LỜI TRỰC TIẾP bằng nội dung bài đăng, tuyệt đối không xin chào, không diễn giải, không nói 'Đây là nội dung...'"
                full_prompt = f"Quy tắc (tuân thủ nghiêm ngặt): {system_rule}\n\nYêu cầu của người dùng: {api_prompt}"
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt
                )
                stt_text = response.text.strip()
                print("\n✅ Gemini API đã trả về nội dung thành công!")
                print(f"👉 Nội dung: {stt_text}\n")
            except ImportError:
                print("⚠️ Lỗi: Bạn chưa cài thư viện google-genai. Vui lòng mở Terminal chạy lệnh: pip install google-genai")
            except Exception as e:
                print(f"⚠️ Lỗi khi gọi Gemini API: {e}")

        if not stt_text or stt_text.lower() == "nan":
            print("❌ Không có nội dung để đăng (trống hoặc nan). Bỏ qua tài khoản này.")
            return False
            
        print("📝 Đang chuẩn bị textbox để nhập nội dung...")
        textbox_xpath = "//div[@role='textbox' and @contenteditable='true']"
        textbox = wait.until(EC.element_to_be_clickable((By.XPATH, textbox_xpath)))
        
        driver.execute_script("arguments[0].click();", textbox)
        time.sleep(1)
        
        if hashtag_text:
            try:
                print(f"✍️ Đang gõ hashtag qua ký tự '#': {hashtag_text}")
                textbox.send_keys("#")
                time.sleep(1)
                
                for char in hashtag_text:
                    textbox.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.1))
                    
                time.sleep(2)
                from selenium.webdriver.common.keys import Keys
                textbox.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.5)
                textbox.send_keys(Keys.ENTER)
                print("✅ Đã chọn gợi ý hashtag đầu tiên.")
                
                textbox.send_keys(" ")
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Lỗi khi nhập hashtag: {e}")

        print("📝 Đang nhập nội dung bài viết chính...")
        for char in stt_text:
            textbox.send_keys(char)
            time.sleep(random.uniform(0.02, 0.08))
            
        time.sleep(2)

        try:
            print("📎 Đang tìm ô upload file...")
            file_input_xpath = "//input[@type='file']"
            file_input = driver.find_element(By.XPATH, file_input_xpath)
            
            if media_paths is None:
                media_paths = []
            valid_paths = [p for p in media_paths if os.path.exists(p)]
            
            if valid_paths:
                print(f"🖼️ Đang đính kèm {len(valid_paths)} file...")
                file_input.send_keys("\n".join(valid_paths))
                time.sleep(3)
            else:
                print(f"⚠️ Không tìm thấy file đính kèm hợp lệ.")
        except Exception as e:
            print(f"⚠️ Không thể đính kèm file: {e}")

        print("🚀 Đang tìm và bấm nút Post...")
        post_btn_xpath = "//div[@role='dialog']//div[@role='button' and (text()='Post' or .//div[text()='Post'] or .//span[text()='Post'])]"
        wait.until(EC.presence_of_element_located((By.XPATH, post_btn_xpath)))
        
        buttons = driver.find_elements(By.XPATH, post_btn_xpath)
        clicked = False
        for btn in buttons:
            if btn.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)
                
                driver.execute_script("arguments[0].click();", btn)
                clicked = True
                print("✅ Đã bấm nút Đăng bài, đang chờ hệ thống xử lý...")
                
                try:
                    success_xpath = "//div[text()='Posted'] | //span[text()='Posted']"
                    wait.until(EC.presence_of_element_located((By.XPATH, success_xpath)))
                    print("🎉 THÀNH CÔNG: Đã xác nhận bài viết được đăng lên Threads!")
                except Exception:
                    print("⚠️ Đã bấm đăng nhưng không nhận được thông báo 'Posted' (Có thể mạng chậm hoặc lỗi).")
                
                break
                
        if not clicked:
            print("⚠️ Không tìm thấy nút Post nào đang hiển thị trên màn hình!")
            return False
            
        wait_time = random.randint(1, 5)
        print(f"🎉 Hoàn tất tài khoản {uid}. Tự động chuyển sang tài khoản tiếp theo sau {wait_time} giây...")
        time.sleep(wait_time)
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi đăng bài cho tài khoản {uid}: {e}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
