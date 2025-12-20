# BioCherish Backend

**BioCherish** is a specialized backend service designed for beetle breeding enthusiasts. It provides a monitoring system for "Kinshi bottles" (fungus bottles), allowing users to track the growth and status of their larvae's environment remotely. 

The system is designed to work with microcontrollers (e.g., ESP32, Raspberry Pi) equipped with cameras and MQTT capabilities to capture and upload bottle images for analysis and logging.



---

##  Features
* **Fungus Bottle Monitoring:** Real-time tracking of bottle status and larval growth.
* **IoT Integration:** Supports MQTT-enabled devices and camera modules.
* **Secure Authentication:** Integrated Google OAuth2 and JWT-based session management.
* **Hardware Security:** Dedicated JWT secret keys for device-to-server authentication.
* **Hybrid Storage:** Scalable AWS DynamoDB integration with local development support.

---

##  Installation

### Prerequisites
- [Docker](https://www.docker.com/get-started/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Recommended) or [Conda](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html)

### 1. Clone the Project
```bash
git clone https://github.com/xxgiasonxx/backend_biocherish.git
cd backend_biocherish
```

### 2. Configure Environment Variables
Copy the example file and update the values to match your configuration:

```bash
cp .env.example .env
```

### 3. Required Variables Breakdown:

* Google OAuth: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI for user login.

* JWT Security: JWT_SECRET_KEY (User sessions) and DEVICE_JWT_SECRET_KEY (Hardware authentication).

* AWS/Database: DATABASE_URL (Use http://localhost:8000 for local Docker) and AWS_REGION.

* Storage: UPLOAD_DIRECTORY (The absolute path where kinshi bottle images will be saved).


## Setup & Execution
### 1. Database Setup
#### Option A: Local Development (Docker)
Run a local instance of AWS DynamoDB:
```bash
docker compose up -d
```

#### Option B: AWS Cloud
Provision a table via the AWS DynamoDB Console and update your .env credentials.

### 2. Environment Setup
#### Option A: Using uv (Fastest)
```bash
uv sync
```

#### Option B: Using conda
```bash
conda create -n biocherish python=3.10.17
conda activate biocherish
pip install -r requirements.txt
```

### 3. Run the Server
#### Option A: Using uv
```bash
uv run main.py
```

#### Option B: Using conda
```bash
python main.py
```

## Hardware Integration
To integrate your own single-chip microcontroller (e.g., ESP32-CAM) with BioCherish:

MQTT Connectivity: Connect to the broker to receive capture triggers or send status heartbeats.

Image Upload: Send a POST request containing the image data to the backend.

Authentication: Include the DEVICE_JWT in the request header to ensure the backend accepts the data.






