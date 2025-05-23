#!/usr/bin/env python3
"""
Callback-Based Snappy Beat-Synced RGBWW Light Controller for Home Assistant

Dependencies:
  pip install requests pyaudio aubio numpy

Usage:
  - Configure HOME_ASSISTANT_URL, TOKEN, LIGHT_IDS, and AUDIO_DEVICE_INDEX below.
  - Run: python3 MusicSync2.py
"""

import time
import requests
import json
import pyaudio
import numpy as np
from aubio import onset
from threading import Thread, Timer
from scipy.signal import butter, lfilter
import random  # if you’re still using random colors

# ————— CONFIGURATION —————
HOME_ASSISTANT_URL = "http://<your-home-assistant>:8123"
TOKEN = "your_long_lived_access_token"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

LIGHT_IDS = ["light.lamp", "light.wiz"]  # Change to your light entity IDs

# Audio settings
FORMAT = pyaudio.paFloat32
CHANNELS = 2
RATE = 44100
FRAMES_PER_BUFFER = 1024
AUDIO_DEVICE_INDEX = 60

# Transition settings
MIN_BRIGHTNESS = 20                 # minimum brightness of the light entities
MAX_BRIGHTNESS = 110                # maximum brightness of the light entities
TRANSITION_UP = 1.2                 # Transiton time to full brightness
TRANSITION_DOWN = 1.2               # Transition time to minimum brightness
DELAY_BEFORE_FADE_DOWN = 1.7        # seconds before fading down

# Bass‐flash cooldown
LAST_BASS_TIME = 0.0                # last time a bass flash was triggered
BASS_COOLDOWN   = 1.5               # seconds cooldown between bass flashes

# Beat-to-light sync delay (seconds)
LIGHT_LATENCY_DELAY = 0.1 # 0.1 for 100 ms helpful if running on networked audio device

# Color palette and cycling, please change to your liking
COLOR_PALETTE = [
    # Brights & Primaries
    [255, 0, 0],         # Bright Red
    [0, 255, 0],         # Bright Green
    [0, 0, 255],         # Bright Blue
    [255, 255, 0],       # Yellow
    [0, 255, 255],       # Cyan
    [255, 0, 255],       # Magenta
    [255, 165, 0],       # Orange

    # Deeper Colors
    [128, 0, 0],         # Maroon
    [0, 0, 128],         # Navy
    [0, 100, 0],         # Dark Green
    [139, 0, 139],       # Dark Magenta
    [85, 107, 47],       # Dark Olive Green
    [70, 130, 180],      # Steel Blue
    [25, 25, 112],       # Midnight Blue
    [72, 61, 139],       # Dark Slate Blue
    [54, 69, 79],        # Dark Slate Gray

    # Neon / Glow Colors
    [57, 255, 20],       # Neon Green
    [255, 20, 147],      # Neon Pink
    [0, 255, 127],       # Spring Green
    [255, 255, 102],     # Neon Yellow
    [0, 191, 255],       # Deep Sky Blue
    [199, 21, 133],      # Medium Violet Red
    [186, 85, 211],      # Medium Orchid
    [127, 255, 212],     # Aquamarine
    [100, 149, 237],     # Cornflower Blue

    # Warm Earthy Tones
    [210, 105, 30],      # Chocolate
    [244, 164, 96],      # Sandy Brown
    [160, 82, 45],       # Sienna
    [205, 133, 63],      # Peru
    [139, 69, 19],       # Saddle Brown
    [255, 228, 181],     # Moccasin
    [255, 222, 173],     # Navajo White
    [250, 128, 114],     # Salmon
    [233, 150, 122],     # Dark Salmon

    # Extra Vivid Colors
    [255, 69, 0],        # Red-Orange
    [128, 0, 128],       # Purple
    [0, 250, 154],       # Medium Spring Green
    [255, 140, 0],       # Dark Orange
    [138, 43, 226],      # Blue Violet
    [153, 50, 204],      # Dark Orchid
    [102, 51, 153],      # Rebecca Purple
    [255, 99, 71],       # Tomato
    [220, 20, 60],       # Crimson
    [255, 215, 0],       # Gold
    [250, 250, 210],     # Light Goldenrod Yellow
]

BEATS_PER_COLOR = 1  # beats before advancing color

# aubio onset detectors
onset_detector        = onset("default", FRAMES_PER_BUFFER, FRAMES_PER_BUFFER, RATE)
energy_onset_detector = onset("energy",  FRAMES_PER_BUFFER, FRAMES_PER_BUFFER, RATE)

beat_counter = 0
current_color = COLOR_PALETTE[0]

# ————— FILTER FUNCTIONS —————
def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    return butter(order, [low, high], btype='band')

def bandpass_filter(data, lowcut, highcut, fs, order=4):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    return lfilter(b, a, data)

def lowpass_filter(data, cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low')
    return lfilter(b, a, data)

# ————— HOME ASSISTANT PULSE HELPERS —————
def instant_pulse(light_id, rgb_color):
    r, g, b = rgb_color
    url = f"{HOME_ASSISTANT_URL}/api/services/light/turn_on"
    up = {
        "entity_id": light_id,
        "rgbww_color": [r, g, b, 0, 0],
        "brightness": MAX_BRIGHTNESS,
        "transition": TRANSITION_UP
    }
    down = {
        "entity_id": light_id,
        "brightness": MIN_BRIGHTNESS,
        "transition": TRANSITION_DOWN
    }
    try:
        requests.post(url, headers=HEADERS, json=up)
        time.sleep(DELAY_BEFORE_FADE_DOWN)
        requests.post(url, headers=HEADERS, json=down)
    except Exception as e:
        print(f"[ERROR] Pulse {light_id}: {e}")

def schedule_pulse(rgb_color):
    for lid in LIGHT_IDS:
        t = Timer(LIGHT_LATENCY_DELAY, instant_pulse, args=(lid, rgb_color))
        t.daemon = True
        t.start()

def instant_bass_flash(light_id):
    url = f"{HOME_ASSISTANT_URL}/api/services/light/turn_on"
    up = {
        "entity_id": light_id,
        "brightness": 225,
        "transition": TRANSITION_UP
    }
    down = {
        "entity_id": light_id,
        "brightness": MIN_BRIGHTNESS,
        "transition": TRANSITION_DOWN
    }
    try:
        requests.post(url, headers=HEADERS, json=up)
        time.sleep(DELAY_BEFORE_FADE_DOWN)
        requests.post(url, headers=HEADERS, json=down)
    except Exception as e:
        print(f"[ERROR] Bass flash {light_id}: {e}")

def schedule_bass_flash():
    for lid in LIGHT_IDS:
        t = Timer(LIGHT_LATENCY_DELAY, instant_bass_flash, args=(lid,))
        t.daemon = True
        t.start()

# Super‐flash at full brightness
def instant_super_flash(light_id):
    url = f"{HOME_ASSISTANT_URL}/api/services/light/turn_on"
    up = {
        "entity_id": light_id,
        "brightness": 255,
        "transition": TRANSITION_UP
    }
    down = {
        "entity_id": light_id,
        "brightness": MIN_BRIGHTNESS,
        "transition": TRANSITION_DOWN
    }
    try:
        requests.post(url, headers=HEADERS, json=up)
        time.sleep(DELAY_BEFORE_FADE_DOWN)
        requests.post(url, headers=HEADERS, json=down)
    except Exception as e:
        print(f"[ERROR] Super flash {light_id}: {e}")

def schedule_super_flash():
    for lid in LIGHT_IDS:
        t = Timer(LIGHT_LATENCY_DELAY, instant_super_flash, args=(lid,))
        t.daemon = True
        t.start()

# ————— AUDIO CALLBACK —————
def audio_callback(in_data, frame_count, time_info, status):
    global beat_counter, LAST_BASS_TIME
    try:
        samples = np.frombuffer(in_data, dtype=np.float32).reshape(-1, 2)
        mono = np.mean(samples, axis=1)

        # Beat‐based color pulse
        beat_samples = bandpass_filter(mono, 30, 16000, RATE).astype(np.float32)
        beat_hit = onset_detector(beat_samples)
        if beat_hit:
            beat_counter += 1
            if beat_counter % BEATS_PER_COLOR == 0:
                current_color = random.choice(COLOR_PALETTE)
            schedule_pulse(current_color)

        # Energy‐based flash (vocals+drums) with cooldown
        now = time.time()
        energy_hit = energy_onset_detector(mono)
        if energy_hit and (now - LAST_BASS_TIME) > BASS_COOLDOWN:
            LAST_BASS_TIME = now
            schedule_bass_flash()

        # Super-flash when both coincide
        if beat_hit and energy_hit and (now - LAST_BASS_TIME) > BASS_COOLDOWN:
            LAST_BASS_TIME = now
            schedule_super_flash()

    except Exception as e:
        print(f"[ERROR] Audio callback: {e}")
    return (None, pyaudio.paContinue)

# ————— MAIN RUNNER —————
if __name__ == "__main__":
    p = pyaudio.PyAudio()
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER,
            input_device_index=AUDIO_DEVICE_INDEX,
            stream_callback=audio_callback
        )
    except Exception as e:
        print(f"[ERROR] Opening audio device {AUDIO_DEVICE_INDEX}: {e}")
        p.terminate()
        exit(1)

    print(f"[AUDIO] Listening on device {AUDIO_DEVICE_INDEX}... Ctrl+C to stop")
    stream.start_stream()
    try:
        while stream.is_active():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[STOP] Exiting...")
    stream.stop_stream()
    stream.close()
    p.terminate()
