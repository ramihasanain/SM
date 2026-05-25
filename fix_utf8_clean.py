import os
import shutil

def restore_and_clean_utf8():
    bak_path = r"c:\Users\ThinkPad\Desktop\مشروع الجامعة\core\api_app\sentiment_engine.py.bak"
    file_path = r"c:\Users\ThinkPad\Desktop\مشروع الجامعة\core\api_app\sentiment_engine.py"
    
    if not os.path.exists(bak_path):
        print("Backup file not found. Make sure you haven't deleted it!")
        return
        
    # First, restore the backup
    shutil.copyfile(bak_path, file_path)
    print("1. Restored original file from backup.")
    
    # Read the restored file as UTF-8, replacing any bad bytes
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        
    try:
        decoded_text = raw_data.decode('utf-8')
        print("2. Success: The file actually decodes as UTF-8 perfectly!")
    except UnicodeDecodeError as e:
        print(f"2. Warning: Found invalid UTF-8 bytes: {e}")
        # Decode replacing bad bytes
        decoded_text = raw_data.decode('utf-8', errors='replace')
        print("   Replaced invalid bytes with replacement characters.")
        
    # Write back as clean UTF-8
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(decoded_text)
    print("3. Successfully saved clean UTF-8 file!")

if __name__ == '__main__':
    restore_and_clean_utf8()
