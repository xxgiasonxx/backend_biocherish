import modal

DOCKER_IMAGE = "esp32-builder"

# 1. 定義環境 (把 Dockerfile 內容搬過來)
image = (
    modal.Image.from_registry("ubuntu:22.04")
    .apt_install("curl", "python3", "python3-pip", "git")
# --- 關鍵：建立軟連結，讓 python 指向 python3 ---
    .run_commands("ln -s /usr/bin/python3 /usr/bin/python")
    .pip_install("esptool") # 加上 fastapi
    .pip_install_from_requirements("requirements.txt")

    .run_commands(
        # 安裝原本 Docker 裡的東西
        "curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh",
        "arduino-cli config init",
        "arduino-cli config set board_manager.additional_urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json",
        "arduino-cli core update-index",
        "arduino-cli core install esp32:esp32",
        "arduino-cli lib install 'PubSubClient' 'ArduinoJson'",
    )
    .env({"PATH": "/usr/local/bin:/bin:/usr/bin"})
    # .add_local_python_source("app")
    .add_local_dir("app", remote_path="/root/app")
    .add_local_dir("certs", remote_path="/root/certs")
    .add_local_dir("zhen_plus_camera", remote_path="/root/zhen_plus_camera")
)

app = modal.App("backend_biocherish", image=image)

# 2. 直接掛載你的整個專案資料夾
# 假設你的 fastapi 代碼在目前資料夾下
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("custom-secret")],
)
@modal.asgi_app()
def fastapi_app():
    from app.main import bio_app
    return bio_app