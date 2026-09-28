import time
import os
import random
from utils.driver_utils import create_driver, calculate_window_pos, extract_and_send_threads_cookie
from config import config
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def comment_on_threads(uid, cookies, proxy_str, ua_str, account_index, mode=1, num_comments=1, content_source="1", api_prompt="", delay_min=1, delay_max=10, keywords="", media_paths=None, excel_path=""):
    """
    Thực hiện comment dạo trên Threads cho một tài khoản.
    Returns:
        bool: True nếu chạy hết luồng không có lỗi chí mạng, False nếu thất bại.
    """
    from features.threads.connect import connect_threads
    from utils.account_utils import update_account_status
    
    print(f"\n🚀 Đang xử lý comment dạo cho tài khoản: {uid}")
    print(f"[{uid}] 🔍 Đang gọi connect_threads để kiểm tra đăng nhập/trạng thái tài khoản...")
    login_result = connect_threads(uid, cookies, proxy_str, ua_str)
    
    if login_result == "die":
        print(f"[{uid}] ❌ Tài khoản đã Die. Cập nhật trạng thái và dừng comment dạo!")
        update_account_status(uid, "Die")
        return False
    elif not login_result:
        print(f"[{uid}] ❌ Đăng nhập thất bại. Dừng comment dạo!")
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
        
        print("🌐 Mở thẳng Threads.net để tiến hành comment dạo...")
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

        # --- Bắt đầu logic comment dạo (Sao chép từ test_random_profile) ---
        saved_search_url = None
        commented_post_urls = set()
        
        for comment_idx in range(num_comments):
            print(f"\n🔄 Bắt đầu comment bài thứ {comment_idx + 1}/{num_comments}...")
            
            if mode == 1:
                print("🌐 Đang tải trang chủ Threads...")
                driver.get("https://www.threads.net/")
                time.sleep(random.uniform(4, 7))
            elif mode == 2:
                if comment_idx == 0 or not saved_search_url:
                    print("🌐 Đang tải trang chủ Threads...")
                    driver.get("https://www.threads.net/")
                    time.sleep(random.uniform(5, 10))
                    
                    if keywords:
                        import urllib.parse
                        kw_list = [k.strip() for k in keywords.split('|') if k.strip()]
                        if kw_list:
                            random_kw = random.choice(kw_list)
                            print(f"👉 Đã chọn từ khóa từ danh sách: {random_kw}")
                            saved_search_url = f"https://www.threads.net/search?q={urllib.parse.quote(random_kw)}"
                            driver.get(saved_search_url)
                            time.sleep(random.uniform(5, 10))
                        else:
                            print("⚠️ Danh sách từ khóa trống, dùng gợi ý ngẫu nhiên.")
                            keywords = "" # fallback

                    if not keywords:
                        print("🔍 Đang truy cập trang tìm kiếm...")
                        driver.get("https://www.threads.net/search")
                        time.sleep(random.uniform(5, 10)) # Đợi trang tìm kiếm tải xong
                        
                        print("🎯 Đang tìm và chọn từ khóa ngẫu nhiên...")
                        keyword_xpath = "//a[@role='link' and contains(@href, '/search?q=')]"
                        try:
                            keyword_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, keyword_xpath)))
                            if keyword_elements:
                                random_el = random.choice(keyword_elements)
                                kw_text = random_el.text.strip()
                                if not kw_text:
                                    # Dự phòng nếu text trống
                                    kw_text = random_el.get_attribute('href').split('q=')[1].split('&')[0]
                                    import urllib.parse
                                    kw_text = urllib.parse.unquote(kw_text)
                                    
                                print(f"👉 Đã chọn từ khóa: {kw_text}")
                                driver.execute_script("arguments[0].click();", random_el)
                                time.sleep(random.uniform(5, 10))
                                saved_search_url = driver.current_url
                            else:
                                print("⚠️ Không tìm thấy từ khóa gợi ý nào.")
                        except Exception as e:
                            print(f"⚠️ Lỗi khi chọn từ khóa: {e}")
                else:
                    print("🌐 Đang tải lại trang tìm kiếm đã lưu...")
                    driver.get(saved_search_url)
                    time.sleep(random.uniform(5, 10))
                
            print("⏳ Đang cuộn xuống tìm nút Comment (Reply)...")
            reply_btn = None
            max_scroll = 20
            for i in range(max_scroll):
                try:
                    # Kiểm tra lỗi "Something went wrong..."
                    error_xpath = "//*[contains(text(), 'Something went wrong, please try again later.')]"
                    if driver.find_elements(By.XPATH, error_xpath):
                        print("⚠️ Gặp lỗi 'Something went wrong...', tiến hành tải lại trang (F5)...")
                        driver.refresh()
                        time.sleep(5)
                except Exception:
                    pass
                    
                try:
                    # Tìm thẻ div có role='button' chứa thẻ svg có thuộc tính title='Reply'
                    xpath = "//div[@role='button' and .//*[local-name()='svg' and @title='Reply']]"
                    elements = driver.find_elements(By.XPATH, xpath)
                    
                    visible_btn = None
                    for el in elements:
                        if el.is_displayed():
                            # Tránh trùng bài viết
                            post_url = ""
                            try:
                                post_link = el.find_element(By.XPATH, "./ancestor::div[@data-pressable-container='true']//a[contains(@href, '/post/')]")
                                post_url = post_link.get_attribute("href")
                            except:
                                pass
                                
                            if post_url and post_url in commented_post_urls:
                                continue # Đã comment bài này, bỏ qua tìm nút của bài dưới
                                
                            visible_btn = el
                            if post_url:
                                commented_post_urls.add(post_url)
                            break
                            
                    if visible_btn:
                        reply_btn = visible_btn
                        print(f"✅ Đã tìm thấy nút Comment ở lần cuộn thứ {i+1}!")
                        break
                except Exception:
                    pass
                    
                # Cuộn xuống một chút nếu chưa thấy
                driver.execute_script("window.scrollBy(0, 600);")
                time.sleep(2)
                
            if reply_btn:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_btn)
                time.sleep(1)
                try:
                    driver.execute_script("arguments[0].click();", reply_btn)
                    print("👆 Đã click vào nút Comment thành công!")
                    
                    # Cuộn trang xuống một chút
                    driver.execute_script("window.scrollBy(0, 300);")
                    time.sleep(3)
                    
                    # Kiểm tra xem có lỗi "Something went wrong" không
                    error_xpath = "//*[contains(text(), 'Something went wrong, please try again later.')]"
                    if driver.find_elements(By.XPATH, error_xpath):
                        print("⚠️ Gặp lỗi 'Something went wrong...' sau khi click nút Comment, tải lại trang (F5) và bỏ qua bài này...")
                        driver.refresh()
                        time.sleep(5)
                        continue
                        
                    # Lấy nội dung comment
                    comment_text = ""
                    if content_source == "2":
                        print("🔄 Đang gọi Gemini API để tạo nội dung comment...")
                        try:
                            from google import genai
                            API_KEY = "YOUR_API_KEY_HERE"
                            client = genai.Client(api_key=API_KEY)
                            
                            system_rule = "Bạn là một chuyên gia tạo content mạng xã hội Threads. Hãy viết nội dung bình luận ngắn gọn, súc tích (1-2 câu), có chứa emoji phù hợp. TRẢ LỜI TRỰC TIẾP bằng nội dung bình luận, tuyệt đối không xin chào, không diễn giải."
                            full_prompt = f"Quy tắc (tuân thủ nghiêm ngặt): {system_rule}\n\nYêu cầu của người dùng: {api_prompt}"
                            
                            response = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=full_prompt
                            )
                            comment_text = response.text.strip()
                            print("\n✅ Gemini API đã trả về nội dung thành công!")
                            print(f"👉 Nội dung: {comment_text}\n")
                        except ImportError:
                            print("⚠️ Lỗi: Bạn chưa cài thư viện google-genai.")
                        except Exception as e:
                            print(f"⚠️ Lỗi khi gọi Gemini API: {e}")
                    else:
                        try:
                            import pandas as pd
                            data_path = excel_path if excel_path else os.path.join(os.getcwd(), "resources", "data.xlsx")
                            if os.path.exists(data_path):
                                df = pd.read_excel(data_path)
                                if not df.empty and 'CONTENT' in df.columns:
                                    random_row = df.sample(n=1)
                                    comment_text = str(random_row.iloc[0]['CONTENT'])
                                    print(f"📝 Đã lấy ngẫu nhiên nội dung bình luận từ data.xlsx")
                        except Exception as e:
                            print(f"⚠️ Lỗi đọc data.xlsx: {e}")
                            
                    if not comment_text or str(comment_text).strip() == "nan":
                        comment_text = "Hay quá!"
                        
                    # Đính kèm ảnh/video (nếu có)
                    if media_paths is None:
                        media_paths = []
                    valid_paths = [p for p in media_paths if os.path.exists(p)]
                    
                    if valid_paths:
                        print(f"📎 Đang đính kèm {len(valid_paths)} file...")
                        try:
                            file_input_xpath = "//input[@type='file']"
                            file_inputs = driver.find_elements(By.XPATH, file_input_xpath)
                            
                            if not file_inputs:
                                print("⚠️ Không thấy <input type='file'>, thử bấm nút 'Attach media'...")
                                try:
                                    attach_btn_xpath = "//div[@role='button' and @aria-label='Attach media']"
                                    attach_btn = driver.find_element(By.XPATH, attach_btn_xpath)
                                    driver.execute_script("arguments[0].click();", attach_btn)
                                    time.sleep(1.5)
                                    file_inputs = driver.find_elements(By.XPATH, file_input_xpath)
                                except Exception as e:
                                    print(f"⚠️ Lỗi khi thử bấm nút Attach media: {e}")

                            if file_inputs:
                                file_inputs[-1].send_keys("\n".join(valid_paths))
                                time.sleep(3) # Đợi upload ảnh
                                print("✅ Đã đính kèm ảnh/video thành công!")
                        except Exception as e:
                            print(f"⚠️ Không thể đính kèm file: {e}")
                        
                    # Tìm textbox nhập nội dung SAU khi đính kèm ảnh
                    textbox_xpath = "//div[@role='textbox' and @contenteditable='true']"
                    textboxes = driver.find_elements(By.XPATH, textbox_xpath)
                    textbox = None
                    for tb in reversed(textboxes):
                        if tb.is_displayed():
                            textbox = tb
                            break
                    if not textbox:
                        textbox = wait.until(EC.presence_of_element_located((By.XPATH, textbox_xpath)))
                        
                    try:
                        driver.execute_script("arguments[0].click();", textbox)
                    except:
                        pass
                    time.sleep(1)
                    
                    print("✍️ Đang nhập nội dung bình luận...")
                    for char in comment_text:
                        try:
                            textbox.send_keys(char)
                        except Exception:
                            tbs = driver.find_elements(By.XPATH, textbox_xpath)
                            for tb in reversed(tbs):
                                if tb.is_displayed():
                                    textbox = tb
                                    break
                            textbox.send_keys(char)
                        time.sleep(random.uniform(0.02, 0.08))
                    time.sleep(1)
                    
                    # Bấm nút Post
                    print("🚀 Đang tìm và bấm nút Đăng (Post/Reply)...")
                    post_btn_xpath = "//div[@role='button' and ( .//*[text()='Post' or text()='Đăng'] or .//*[local-name()='svg' and @aria-label='Reply'] )]"
                    
                    try:
                        post_btns = wait.until(EC.presence_of_all_elements_located((By.XPATH, post_btn_xpath)))
                        post_btn = None
                        for btn in reversed(post_btns):
                            if btn.is_displayed():
                                post_btn = btn
                                break
                        if not post_btn:
                            post_btn = post_btns[-1]
                            
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_btn)
                        except:
                            pass
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", post_btn)
                        print("✅ Đã bấm nút Đăng bình luận!")
                        
                        try:
                            success_xpath = "//*[text()='Posted' or text()='Đã đăng']"
                            wait.until(EC.presence_of_element_located((By.XPATH, success_xpath)))
                            print("🎉 THÀNH CÔNG: Đã xác nhận bình luận được đăng!")
                        except Exception:
                            print("⚠️ Không nhận được thông báo 'Posted', nhưng vẫn tiếp tục...")
                            
                    except Exception as e:
                        print(f"⚠️ Không tìm thấy nút Đăng bình luận: {e}")
                        
                except Exception as e:
                    print(f"⚠️ Lỗi trong quá trình nhập bình luận: {e}")
            else:
                print("⚠️ Đã cuộn nhiều lần nhưng không tìm thấy nút Comment nào.")
                
            if comment_idx < num_comments - 1:
                delay = random.uniform(delay_min, delay_max)
                print(f"⏳ Đợi {delay:.1f} giây trước khi comment bài tiếp theo...")
                time.sleep(delay)

        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi comment dạo: {e}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
