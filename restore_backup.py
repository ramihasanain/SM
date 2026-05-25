import shutil
import os

def restore():
    bak_path = r"c:\Users\ThinkPad\Desktop\مشروع الجامعة\core\api_app\sentiment_engine.py.bak"
    file_path = r"c:\Users\ThinkPad\Desktop\مشروع الجامعة\core\api_app\sentiment_engine.py"
    
    if os.path.exists(bak_path):
        shutil.copyfile(bak_path, file_path)
        print("Restored original file from backup!")
    else:
        print("Backup file does not exist!")

if __name__ == '__main__':
    restore()
