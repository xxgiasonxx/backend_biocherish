import glob
import os
import subprocess
from app.core.config import Settings
import time
import shutil

# --- 設定區 ---
SKETCH_NAME = "zhen_plus_camera"
DOCKER_IMAGE = "esp32-builder"

def put_data(WIFI_SSID: str = "", WIFI_PASSWORD: str = "", AWS_IOT_ENDPOINT: str = "", DEVICE_ID: str = "", CERT_CA: str = "", CERT_CRT: str = "", CERT_PRIVATE: str = "") -> str:
    WIFI_SSID = WIFI_SSID.replace(' ', '').replace('\n', '')
    WIFI_PASSWORD = WIFI_PASSWORD.replace(' ', '').replace('\n', '')
    AWS_IOT_ENDPOINT = AWS_IOT_ENDPOINT.replace(' ', '').replace('\n', '')
    DEVICE_ID = DEVICE_ID.replace(' ', '').replace('\n', '')
    CERT_CA = CERT_CA.strip()
    CERT_CRT = CERT_CRT.strip()
    CERT_PRIVATE = CERT_PRIVATE.strip()
    # (保持原樣，產生 secrets.h 內容)
    return f"""#ifndef SECRETS_H  
#define SECRETS_H
#include <pgmspace.h>

const char WIFI_SSID[] = "{WIFI_SSID}";
const char WIFI_PASSWORD[] = "{WIFI_PASSWORD}";
const char AWS_IOT_ENDPOINT[] = "{AWS_IOT_ENDPOINT}";
const char DEVICE_ID[] = "{DEVICE_ID}";

static const char AWS_CERT_CA[] PROGMEM = R"EOF(
{CERT_CA}
)EOF";

static const char AWS_CERT_CRT[] PROGMEM = R"EOF(
{CERT_CRT}
)EOF";

static const char AWS_CERT_PRIVATE[] PROGMEM = R"EOF(
{CERT_PRIVATE}
)EOF";
#endif
"""

def run_build(device_id: str, secrets_content: str, settings=Settings()):
    # 0. 準備目標資料夾路徑
    target_dir = os.path.join(settings.FILE_FOLDER, device_id)
    os.makedirs(target_dir, exist_ok=True) # 自動建立 device-files/{device_id}/

    # 1. 確保原始碼目錄存在並寫入 secrets.h
    if not os.path.exists(SKETCH_NAME):
        os.makedirs(SKETCH_NAME)
    
    with open(f"{SKETCH_NAME}/secrets.h", "w", encoding="utf-8") as f:
        f.write(secrets_content)
    print(f"[{device_id}] 已更新 secrets.h")

    # 3. 使用 Docker 同時進行編譯與合併
    # 我們將合併指令也寫入 Docker 執行序列
    output_filename = f"{device_id}.bin"
    
    # 這裡我們用 bash 串聯多個指令：編譯 -> 合併
    docker_shell_cmd = (
        f"arduino-cli compile --fqbn esp32:esp32:esp32cam --output-dir ./build {SKETCH_NAME} && "
        f"python3 -m esptool --chip esp32 merge_bin "
        f"-o ./build/{output_filename} "
        f"--flash_mode dio --flash_size 4MB "
        f"0x1000 ./build/{SKETCH_NAME}.ino.bootloader.bin "
        f"0x8000 ./build/{SKETCH_NAME}.ino.partitions.bin "
        f"0x10000 ./build/{SKETCH_NAME}.ino.bin"
    )

    is_running_in_modal = os.environ.get("MODAL_IMAGE_ID") is not None

    if is_running_in_modal:
        # ☁️ 雲端模式：直接執行指令！
        # 因為你的 Image 已經安裝了 arduino-cli 和 python3，直接跑就好
        print("Running native command in Modal...")
        subprocess.run(docker_shell_cmd, shell=True, check=True)

    else:
        # 💻 本地模式：使用 Docker
        # 這保留給你本地開發用
        compile_and_merge_cmd = [
            "docker", "run", "--rm",
            "-v", f"{os.getcwd()}:/app",
            DOCKER_IMAGE,
            "bash", "-c", docker_shell_cmd
        ]

        print(f"[{device_id}] 正在 Docker 內編譯與合併...")
        subprocess.run(compile_and_merge_cmd, check=True)

    # 4. 將產出的檔案從 build 移動到指定的 device-files 目錄
    source_path = os.path.join("build", output_filename)
    target_path = os.path.join(settings.FILE_FOLDER, device_id, output_filename)
    
    if os.path.exists(source_path):
        import shutil
        shutil.move(source_path, target_path)
        print(f"✅ 完成！檔案已搬移至: {target_path}")
        return os.path.abspath(target_path)
    else:
        print("❌ 錯誤：Docker 跑完了，但沒看到合併後的檔案。")
        return None

def build_zip(device_id: str, secrets_content: str, settings=Settings()):
    print(f"📦 [Zip] 開始打包程序: Device ID {device_id}")

    original_sketch_path = os.path.abspath(SKETCH_NAME)
    temp_root = f"/tmp/build_{device_id}"
    temp_sketch_path = os.path.join(temp_root, SKETCH_NAME)
    
    output_dir = os.path.join(settings.FILE_FOLDER, device_id)
    zip_base_name = os.path.join(output_dir, device_id)

    try:
        # 1. 清理與複製
        if os.path.exists(temp_root):
            shutil.rmtree(temp_root)
        
        shutil.copytree(
            original_sketch_path, 
            temp_sketch_path,
            ignore=shutil.ignore_patterns('.git', '.github', '__pycache__', 'build', 'device-files', '*.zip', 'node_modules')
        )

        # 2. 寫入 secrets.h
        secrets_file_path = os.path.join(temp_sketch_path, "secrets.h")
        with open(secrets_file_path, "w", encoding="utf-8") as f:
            f.write(secrets_content)

        # ==========================================
        # 🕒 關鍵修正：強制更新檔案時間戳記
        # ==========================================
        print("🕒 正在修正所有檔案與資料夾的時間戳記...")
        now = time.time()
        
        # 1. 先修正主資料夾本身
        os.utime(temp_sketch_path, (now, now))
        
        # 2. 遍歷修正內容（包含 root 目錄本身）
        for root, dirs, files in os.walk(temp_sketch_path):
            for item in dirs + files:
                full_path = os.path.join(root, item)
                try:
                    os.utime(full_path, (now, now))
                except Exception:
                    pass # 防止極少數權限問題導致中斷
        # ==========================================

        # 3. 壓縮
        os.makedirs(output_dir, exist_ok=True)

        shutil.make_archive(
            base_name=zip_base_name, 
            format='zip', 
            root_dir=temp_root, 
            base_dir=SKETCH_NAME
        )
        
        final_zip_path = f"{zip_base_name}.zip"
        print(f"✅ [Zip] 打包成功: {final_zip_path}")
        return os.path.abspath(final_zip_path)

    except Exception as e:
        print(f"❌ [Zip] 打包失敗: {str(e)}")
        raise e

    finally:
        if os.path.exists(temp_root):
            shutil.rmtree(temp_root)
            print("🧹 [Zip] 暫存區已清理")
