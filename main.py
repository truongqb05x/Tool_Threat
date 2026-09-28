# -*- coding: utf-8 -*-
import sys
from utils.account_utils import read_all_accounts_data
from features.threads.connect import connect_threads, open_chrome_only
from features.post_threads.post_threads import post_to_threads
from features.comment_threads.comment_threads import comment_on_threads
from features.farm_threads.farm_threads import farm_threads

# Fix encoding issue on Windows
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "open_chrome" and len(sys.argv) > 2:
            target_uid = sys.argv[2]
            accounts = read_all_accounts_data()
            if not accounts:
                return
            
            for uid, cookies, proxy_str, ua_str, cookie_threads in accounts:
                if uid == target_uid:
                    open_chrome_only(uid, proxy_str, ua_str)
                    return
            return
        elif sys.argv[1] == "connect_thread" and len(sys.argv) > 2:
            target_uid = sys.argv[2]
            accounts = read_all_accounts_data()
            if not accounts:
                return
            
            for uid, cookies, proxy_str, ua_str, cookie_threads in accounts:
                if uid == target_uid:
                    connect_threads(uid, cookies, proxy_str, ua_str)
                    return
            return
        elif sys.argv[1] == "post_thread" and len(sys.argv) > 2:
            target_uid = sys.argv[2]
            content_source = sys.argv[3] if len(sys.argv) > 3 else "1"
            api_prompt = sys.argv[4] if len(sys.argv) > 4 else ""
            hashtag_text = sys.argv[5] if len(sys.argv) > 5 else ""
            media_paths_str = sys.argv[6] if len(sys.argv) > 6 else ""
            excel_path = sys.argv[7] if len(sys.argv) > 7 else ""
            media_paths = [p for p in media_paths_str.split("|") if p.strip()] if media_paths_str else []
            
            accounts = read_all_accounts_data()
            if not accounts:
                return
            
            for idx, (uid, cookies, proxy_str, ua_str, cookie_threads) in enumerate(accounts):
                if uid == target_uid:
                    post_to_threads(uid, cookies, proxy_str, ua_str, idx, cookie_threads, content_source, api_prompt, hashtag_text, media_paths, excel_path)
                    return
            return
        elif sys.argv[1] == "comment_thread" and len(sys.argv) > 2:
            target_uid = sys.argv[2]
            mode = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            num_comments = int(sys.argv[4]) if len(sys.argv) > 4 else 1
            delay_min = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
            delay_max = float(sys.argv[6]) if len(sys.argv) > 6 else 10.0
            keywords = sys.argv[7] if len(sys.argv) > 7 else ""
            content_source = sys.argv[8] if len(sys.argv) > 8 else "1"
            api_prompt = sys.argv[9] if len(sys.argv) > 9 else ""
            media_paths_str = sys.argv[10] if len(sys.argv) > 10 else ""
            excel_path = sys.argv[11] if len(sys.argv) > 11 else ""
            media_paths = [p for p in media_paths_str.split("|") if p.strip()] if media_paths_str else []
            
            accounts = read_all_accounts_data()
            if not accounts:
                return
            
            for idx, (uid, cookies, proxy_str, ua_str, cookie_threads) in enumerate(accounts):
                if uid == target_uid:
                    comment_on_threads(uid, cookies, proxy_str, ua_str, idx, cookie_threads, mode, num_comments, content_source, api_prompt, delay_min, delay_max, keywords, media_paths, excel_path)
                    return
            return
        elif sys.argv[1] == "farm_thread" and len(sys.argv) > 2:
            # args: farm_thread <uid> <is_scroll> <is_like> <like_delay_min> <like_delay_max> <is_read_notif> <notif_count> <total_mins>
            target_uid = sys.argv[2]
            
            is_scroll = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            is_like = int(sys.argv[4]) if len(sys.argv) > 4 else 1
            like_delay_min = int(sys.argv[5]) if len(sys.argv) > 5 else 10
            like_delay_max = int(sys.argv[6]) if len(sys.argv) > 6 else 30
            is_read_notif = int(sys.argv[7]) if len(sys.argv) > 7 else 1
            notif_count = int(sys.argv[8]) if len(sys.argv) > 8 else 2
            total_mins = int(sys.argv[9]) if len(sys.argv) > 9 else 30
            
            accounts = read_all_accounts_data()
            if not accounts:
                return
            
            for idx, (uid, cookies, proxy_str, ua_str, cookie_threads) in enumerate(accounts):
                if uid == target_uid:
                    farm_threads(uid, cookies, proxy_str, ua_str, idx, cookie_threads, is_scroll, is_like, like_delay_min, like_delay_max, is_read_notif, notif_count, total_mins)
                    return
            return

    while True:
        print("\n" + "="*40)
        print("          MENU CHỨC NĂNG")
        print("="*40)
        print("1. Kết nối với threads")
        print("2. Đăng bài lên Threads")
        print("3. Comment dạo trên Threads")
        print("4. Tương tác / Nuôi tài khoản")
        print("0. Thoát")
        print("="*40)
        choice = input("👉 Nhập lựa chọn của bạn: ").strip()
        
        if choice == "1":
            accounts = read_all_accounts_data()
            if not accounts:
                print("⚠️ Lỗi: Không thể tải dữ liệu tài khoản, vui lòng kiểm tra resources/account.txt")
            else:
                for uid, cookies, proxy_str, ua_str, cookie_threads in accounts:
                    success = connect_threads(uid, cookies, proxy_str, ua_str)
                    if success in [False, "die"]:
                        print(f"⏭️ Bỏ qua tài khoản {uid}, chuyển sang tài khoản tiếp theo...")
                print("\n✅ Đã duyệt xong toàn bộ tài khoản trong file!")
            break
        elif choice == "2":
            accounts = read_all_accounts_data()
            if not accounts:
                print("⚠️ Lỗi: Không thể tải dữ liệu tài khoản, vui lòng kiểm tra resources/account.txt")
            else:
                print("\nChọn nguồn nội dung bài viết:")
                print("1. Lấy từ file Excel (resources/data.xlsx)")
                print("2. Lấy từ API (Gemini)")
                content_source = input("👉 Nhập lựa chọn (1/2) [Mặc định: 1]: ").strip()
                
                if content_source not in ["1", "2"]:
                    content_source = "1"
                    
                api_prompt = ""
                if content_source == "2":
                    api_prompt = input("\n👉 Nhập yêu cầu/prompt cho AI (VD: Viết một câu nói hay về tình yêu): ").strip()
                    if not api_prompt:
                        api_prompt = "Viết một status thả thính vui nhộn, ngắn gọn, phù hợp với mạng xã hội Threads."
                        
                hashtag_text = input("\n👉 Nhập hashtag muốn thêm (để trống nếu không thêm): ").strip()
                
                for idx, (uid, cookies, proxy_str, ua_str, cookie_threads) in enumerate(accounts):
                    success = post_to_threads(uid, cookies, proxy_str, ua_str, idx, cookie_threads, content_source, api_prompt, hashtag_text, [])
                    if not success:
                        print(f"⏭️ Bỏ qua tài khoản {uid}, chuyển sang tài khoản tiếp theo...")
                print("\n✅ Đã duyệt xong toàn bộ tài khoản trong file!")
            break
        elif choice == "3":
            accounts = read_all_accounts_data()
            if not accounts:
                print("⚠️ Lỗi: Không thể tải dữ liệu tài khoản, vui lòng kiểm tra resources/account.txt")
            else:
                print("\n👉 Chọn chế độ comment:")
                print("  1 - Comment trên Newfeed")
                print("  2 - Comment theo từ khóa")
                mode_input = input("Nhập lựa chọn [Mặc định: 1]: ").strip()
                mode = int(mode_input) if mode_input.isdigit() else 1
                
                num_input = input("\n👉 Nhập số lượng bài cần comment [Mặc định: 1]: ").strip()
                num_comments = int(num_input) if num_input.isdigit() else 1
                
                for idx, (uid, cookies, proxy_str, ua_str, cookie_threads) in enumerate(accounts):
                    success = comment_on_threads(uid, cookies, proxy_str, ua_str, idx, cookie_threads, mode, num_comments)
                    if not success:
                        print(f"⏭️ Bỏ qua tài khoản {uid}, chuyển sang tài khoản tiếp theo...")
                print("\n✅ Đã duyệt xong toàn bộ tài khoản trong file!")
            break
        elif choice == "4":
            accounts = read_all_accounts_data()
            if not accounts:
                print("⚠️ Lỗi: Không thể tải dữ liệu tài khoản, vui lòng kiểm tra resources/account.txt")
            else:
                is_scroll = 1
                is_like = 1
                like_delay_min = 10
                like_delay_max = 30
                is_read_notif = 1
                notif_count = 2
                total_mins = 30
                
                print("Chức năng chạy thủ công với thông số mặc định (để tinh chỉnh vui lòng dùng giao diện XAML).")
                
                for idx, (uid, cookies, proxy_str, ua_str, cookie_threads) in enumerate(accounts):
                    success = farm_threads(uid, cookies, proxy_str, ua_str, idx, cookie_threads, is_scroll, is_like, like_delay_min, like_delay_max, is_read_notif, notif_count, total_mins)
                    if not success:
                        print(f"⏭️ Bỏ qua tài khoản {uid}, chuyển sang tài khoản tiếp theo...")
                print("\n✅ Đã duyệt xong toàn bộ tài khoản trong file!")
            break
        elif choice == "0":
            print("👋 Đã thoát chương trình.")
            break
        else:
            print("⚠️ Lựa chọn không hợp lệ. Vui lòng thử lại!")

if __name__ == "__main__":
    main()