from app.core.config import Settings
from typing import Optional, Dict

import os
import requests

def device_is_connected(device_id: str, settings: Settings) -> bool:
    response = requests.get(f'{settings.DATA_URL}/iot/devices/{device_id}/connection')
    if response.status_code != 200:
        return False
    data = response.json()
    if data.get('message', '') == 'Device is connected':
        return True
    return False

def find_bottle_and_env_state(bottle_id: int, env_id: int, settings: Settings):
    detect_record_states = requests.get(f'{settings.DATA_URL}/db/device_record_states')
    detect_record_states = detect_record_states.json()
    detect_record_states = detect_record_states.get("detect_record_states", [])

    bottle_state, env_state = {}, {}

    for drs in detect_record_states:
        if drs['detect_record_state_id'] == bottle_id:
            bottle_state = drs
        if drs['detect_record_state_id'] == env_id:
            env_state = drs
    return bottle_state, env_state

def find_all_bottle_and_env_state(settings: Settings):
    detect_record_states = requests.get(f'{settings.DATA_URL}/db/device_record_states')
    detect_record_states = detect_record_states.json()
    detect_record_states = detect_record_states.get("detect_record_states", [])

    return detect_record_states

def find_bottle_state(state, bottle_id: int):
    bottle_state = {}

    for drs in state:
        if drs['detect_record_state_id'] == bottle_id:
            bottle_state = drs
            return bottle_state
    return None



# def find_bottle_state(bottle_id: int, settings: Settings):
#     detect_record_states = requests.get(f'{settings.DATA_URL}/db/device_record_states')
#     detect_record_states = detect_record_states.json()
#     detect_record_states = detect_record_states.get("detect_record_states", [])

#     bottle_state = {}

#     for drs in detect_record_states:
#         if drs['detect_record_state_id'] == bottle_id:
#             bottle_state = drs
#             return bottle_state
#     return None

def get_last_detect_record(device_id: str, settings: Settings):
    detect_record = requests.get(f'{settings.DATA_URL}/db/devices/{device_id}/detect_records')
    detect_record = detect_record.json()
    detect_record = detect_record.get("detect_records", [])
    detect_record = detect_record[-1] if detect_record else None

    if detect_record:
        bottle_state, env_state = find_bottle_and_env_state(detect_record['bottleStateID'], detect_record.get('envStateID', ''), settings)
        detect_record['detect_record_state'] = bottle_state
        detect_record['env_record_state'] = env_state
        return detect_record

    return None

def get_bottle_detect_state_history(device_id: str, s: Optional[int], e: Optional[int], settings: Settings):
    params = {}
    if s is not None:
        params['s'] = s
    if e is not None:
        params['e'] = e
    detect_records = requests.get(f'{settings.DATA_URL}/db/devices/{device_id}/detect_records', params=params)
    detect_records = detect_records.json()
    detect_records = detect_records.get("detect_records", [])
    return detect_records

def split_all_detect_state_history(all_scans, s: Optional[int], e: Optional[int], settings: Settings):
    all_scans.sort(key=lambda x: x['detectTime'], reverse=True)

    scans = all_scans[s:e]


    return scans

def find_detect_record(device_id: str, detect_record_id: str, settings: Settings):
    all_records = get_bottle_detect_state_history(device_id, None, None, settings)
    for record in all_records:
        if record['detect_record_id'] == detect_record_id:
            bottle_state, env_state = find_bottle_and_env_state(record['bottleStateID'], record.get('envStateID', ''), settings)
            record['detect_record_state'] = bottle_state
            record['env_record_state'] = env_state
            return record
    return None

def find_all_detect_record_with_detect_record_state(device_id: str, detect_record_id: str, settings: Settings):
    all_records = get_bottle_detect_state_history(device_id, 0, None, settings)
    for record in all_records:
        if record['detect_record_id'] == detect_record_id:
            bottle_state = find_bottle_state(record['bottleStateID'], settings)
            record['detect_record_state'] = bottle_state
    return all_records

def get_device_info(device_id: str, settings: Settings):
    device_info = requests.get(
        f'{settings.DATA_URL}/db/devices/{device_id}'
    )
    device_info = device_info.json()

    return device_info

def update_device_info(data: Dict, settings: Settings):
    device_info = get_device_info(data.get("device_id", ""), settings)

    if not device_info:
        return False

    device_info['detectFreq'] = data.get("detectFreq", device_info.get("detectFreq", 30))
    device_info['name'] = data.get("name", device_info.get("name", ""))

    response = requests.put(
        f'{settings.DATA_URL}/db/devices/{data["device_id"]}',
        json=device_info
    )
    return response.status_code == 200

def manual_scan_bottle(file, temperature: Optional[int], humidity: Optional[int], settings: Settings) -> Dict:

    files = {
        # image 對應 UploadFile / multipart 檔案
        "image": (file.filename, file.file, file.content_type),
    }

    data = {
        "temperature": temperature if temperature else 0,
        "humidity": humidity if humidity else 0,
    }

    response = requests.post(
        f'{settings.DATA_URL}/db/manual_detect_records',
        files=files,
        data=data,
    )
    response = response.json()
    print(response)

    return response

def create_new_device(device_id: str, name: str, freq: int, settings: Settings) -> Dict:

    response = requests.post(
        f'{settings.DATA_URL}/db/devices',
        json={
            "device_id": device_id,
            "name": name,
        }
    )
    response = response.json()
    print(response)
    if response.get("device_id", "") != device_id:
        return None

    return response

def get_os_file_content(file_url: str) -> bytes:
    with open(file_url, 'rb') as f:
        content = f.read()
    # 同時移除 Unix (\n) 與 Windows (\r\n) 的換行符號
    return content
    

def update_device_all_info(device_id: str, name: str, freq: int, endpoint: str, CRT: str, PRIVATE: str, settings: Settings) -> bool:

    device_info = get_device_info(device_id, settings)

    if not device_info:
        return False

    device_info['detectFreq'] = freq
    device_info['name'] = name
    device_info['endpoint'] = endpoint
    device_info['certificate'] = CRT
    device_info['privateKey'] = PRIVATE
    device_info.pop('device_id', None)
    device_info.pop('lastEditTime', None)

    response = requests.put(
        f'{settings.DATA_URL}/db/devices/{device_id}',
        json=device_info
    )
    return response.status_code == 200

def manual_device_shot(device_id: str, settings: Settings) -> bool:

    response = requests.post(
        f'{settings.DATA_URL}/iot/devices/{device_id}/manual_trigger'
    )
    print(response)
    return response.status_code == 200