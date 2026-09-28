import os

def read_all_accounts_data(file_path="resources/account.txt"):
    """
    Reads the account file and extracts UID and cookies for all accounts.
    Format: uid|password|cookie|token...
    Returns: A list of tuples [(uid, cookies), (uid, cookies), ...]
    """
    accounts = []
    
    #print("🍪 Đang đọc toàn bộ tài khoản và cookie...")
    try:
        if not os.path.exists(file_path):
            print(f"⚠️ Không tìm thấy file {file_path}")
            return accounts
            
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) >= 3:
                    uid = parts[0]
                    import time
                    expiry_time = int(time.time()) + 365 * 24 * 3600 # 1 năm
                    
                    cookie_str = parts[3] if len(parts) > 3 else ""
                    cookies = []
                    for c in cookie_str.split(";"):
                        c = c.strip()
                        if "=" in c:
                            k, v = c.split("=", 1)
                            cookies.append({
                                "name": k.strip(), 
                                "value": v.strip(), 
                                "domain": ".instagram.com", 
                                "path": "/",
                                "expiry": expiry_time
                            })
                    
                    proxy_str = parts[8].strip() if len(parts) > 8 else None
                    ua_str = parts[9].strip() if len(parts) > 9 else None
                    cookie_threads = parts[4].strip() if len(parts) > 4 else ""
                    
                    accounts.append((uid, cookies, proxy_str, ua_str, cookie_threads))
                else:
                    print(f"⚠️ Dòng {i+1} trong file tài khoản không đúng định dạng.")
                    
        #print(f"✅ Đã tìm thấy {len(accounts)} tài khoản hợp lệ.")
    except Exception as e:
        print(f"⚠️ Lỗi khi đọc dữ liệu tài khoản: {e}")
        
    return accounts

def update_account_status(uid, new_status, file_path="resources/account.txt"):
    try:
        if not os.path.exists(file_path):
            return False
            
        with open(file_path, "r", encoding="utf-8") as f_in:
            lines = f_in.readlines()
            
        with open(file_path, "w", encoding="utf-8") as f_out:
            for line in lines:
                parts = line.strip().split("|")
                if parts and parts[0] == uid:
                    # Mở rộng mảng lên ít nhất 11 phần tử (để index 10 tồn tại)
                    while len(parts) < 11:
                        parts.append("")
                    parts[10] = new_status
                    f_out.write("|".join(parts) + "\n")
                    print(f"✅ Đã ghi trạng thái mới {new_status} cho {uid}")
                else:
                    f_out.write(line)
        return True
    except Exception as e:
        print(f"⚠️ Lỗi khi cập nhật trạng thái account {uid}: {e}")
        return False
