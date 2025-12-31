FROM ubuntu:22.04

# 安裝基礎工具與 Python
RUN apt-get update && apt-get install -y \
    curl python3 python3-pip git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install esptool

# 安裝 Arduino CLI
RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
ENV PATH=$PATH:/bin

# 配置 ESP32 環境
RUN arduino-cli config init
RUN arduino-cli config set board_manager.additional_urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
RUN arduino-cli core update-index
RUN arduino-cli core install esp32:esp32

RUN arduino-cli lib install "PubSubClient"

RUN arduino-cli lib install "ArduinoJson"

# 設定工作目錄
WORKDIR /app