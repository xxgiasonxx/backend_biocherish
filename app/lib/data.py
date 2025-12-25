from app.core.config import Settings
from typing import Optional, Dict
import requests

def device_is_connected(device_id: str, settings: Settings) -> bool:
    response = requests.get(f'{settings.DEVICE_URL}/iot/devices/{device_id}/connection')
    if response.status_code != 200:
        return False
    data = response.json()
    if data.get('message', '') == 'Device is connected':
        return True
    return False

def find_bottle_and_env_state(bottle_id: str, env_id: str, settings: Settings):
    detect_record_states = requests.get(f'{settings.DATA_URL}/db/detect_record_states')
    detect_record_states = detect_record_states.json()
    detect_record_states = detect_record_states.get("detect_record_states", [])

    bottle_state, env_state = None, None

    for drs in detect_record_states:
        if drs['detect_record_state_id'] == bottle_id:
            bottle_state = drs
        if drs['detect_record_state_id'] == env_id:
            env_state = drs
    return bottle_state, env_state

def get_last_detect_record(bottle_id: str, settings: Settings):
    detect_record = requests.get(f'{settings.DATA_URL}/db/device/{bottle_id}/detect_records?e=1')
    detect_record = detect_record.json()
    detect_record = detect_record.get("detect_records", [])[0] if detect_record.get("detect_records", []) else None

    if detect_record:
        bottle_state, env_state = find_bottle_and_env_state(detect_record['bottleStateID'], detect_record.get('envStateID', ''), settings)
        detect_record['detect_record_state'] = bottle_state
        detect_record['env_record_state'] = env_state
        return detect_record

    return None

def get_bottle_detect_state_history(bottle_id: str, s: Optional[int], e: Optional[int], settings: Settings):
    params = {}
    if s is not None:
        params['s'] = s
    if e is not None:
        params['e'] = e
    detect_records = requests.get(f'{settings.DATA_URL}/db/device/{bottle_id}/detect_records', params=params)
    detect_records = detect_records.json()
    detect_records = detect_records.get("detect_records", [])
    return detect_records

def find_detect_record(bottle_id: str, detect_record_id: str, settings: Settings):
    all_records = get_bottle_detect_state_history(bottle_id, None, None, settings)
    for record in all_records:
        if record['detect_record_id'] == detect_record_id:
            bottle_state, env_state = find_bottle_and_env_state(record['bottleStateID'], record.get('envStateID', ''), settings)
            record['detect_record_state'] = bottle_state
            record['env_record_state'] = env_state
            return record
    return None

def get_device_info(device_id: str, settings: Settings):
    device_info = requests.get(
        f'{settings.DATA_URL}/db/devices/${device_id}'
    )
    device_info = device_info.json()

    return device_info

def update_device_info(data: Dict, settings: Settings):
    device_info = get_device_info(data["device_id"], settings)

    if not device_info:
        return False

    device_info['detectFreq'] = data.get("detectFreq", device_info.get("detectFreq", 30))

    response = requests.put(
        f'{settings.DATA_URL}/db/device/{data["device_id"]}',
        json=device_info
    )
    return response.status_code == 200