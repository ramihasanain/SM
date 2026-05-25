import os

def detect_and_convert():
    file_path = r"c:\Users\ThinkPad\Desktop\مشروع الجامعة\core\api_app\sentiment_engine.py"
    encodings = ['utf-8', 'cp1256', 'windows-1256', 'latin-1', 'utf-16']
    
    content = None
    used_encoding = None
    
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
            used_encoding = enc
            print(f"Successfully read file with encoding: {enc}")
            break
        except UnicodeDecodeError:
            continue
            
    if not content:
        print("Failed to read file with any of the common encodings.")
        return
        
    # Write backup
    backup_path = file_path + ".bak"
    with open(backup_path, 'w', encoding=used_encoding) as f:
        f.write(content)
    print(f"Saved backup to: {backup_path}")
    
    # Write as UTF-8
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully re-saved file in UTF-8 encoding!")

if __name__ == '__main__':
    detect_and_convert()
