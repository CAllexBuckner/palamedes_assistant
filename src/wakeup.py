import os

import sounddevice as sd
import numpy as numpy
import scipy.signal
import yaml

def load_config(config_path: str) -> dict:
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as config:
                loaded_data = yaml.safe_load(config)
        except Exception as e:
            print(f"Config Error: {e}. Config does not exist!")
    return loaded_data

def resolve_input_device(config: dict) -> None | int:
    device_request = config.get("input_device")
    if device_request in (None, ""):
        return None
    try:
        devices = sd.query_devices()
    except Exception as e:
        print(f"[Audio] Device query failed {e}", flush=True)
        return None

    if isinstance(device_request, int) or (isinstance(device_request, str)) and device_request.isdigit():
        index = int(device_request)
        if 0 <= index < len(devices):
            return index
        print(f"[AUDIO] Input device index not found: {index}", flush=True)
        return None

    requested_lower = str(device_request).lower()
    for idx, dev in enumerate(devices):
        print(f"[AUDIO DEBUG] Index {idx}: {dev.get('name')} (In: {dev.get('max_input_channels')})", flush=True) # DEBUG LINE
        if dev.get("max_input_channels", 0) > 0 and requested_lower in dev.get("name", "").lower():
            return idx

        print(f"[AUDIO] Input device name not found: {requested}", flush=True)
    return None

    INPUT_DEVICE_NAME = resolve_input_device(load_config("config.yaml").get("input_device"))
    if INPUT_DEVICE_NAME is not None:
        try:
            device_info = sd.query_devices(INPUT_DEVICE_NAME)
            print(f"[AUDIO] Using input device: {device_info.get('name', INPUT_DEVICE_NAME)}", flush=True)
        except Exception:
            print(f"[AUDIO] Using input device index: {INPUT_DEVICE_NAME}", flush=True)

def choose_input_samplerate(device: str, preferred=None) -> int:
    candidates = []
    if preferred:
        candidates.append(preferred)
    try:
        device_info = sd.query_devices(device)
        print(f"[AUDIO DEBUG] Device Info: {device_info}", flush=True) # DEBUG
        if "default_samplerate" in device_info:
            candidates.append(int(device_info["default_samplerate"]))
    except Exception as e:
        print(f"[AUDIO DEBUG] Query failed: {e}", flush=True)
        pass

    candidates.extend([48000, 44100, 32000, 16000])
    seen = set()
    for rate in candidates:
        if not rate or rate in seen:
            continue
        seen.add(rate)
        try:
            sd.check_input_settings(device=device, samplerate=rate, channels=1, dtype="int16")
            return rate
        except Exception:
            continue

    return int(candidates[0]) if candidates else 44100
