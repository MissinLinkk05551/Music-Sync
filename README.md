# 🎵 Music-Synced Lights for Home Assistant

Sync your Home Assistant smart lights with music playing on your PC using real-time audio analysis powered by Python, PyAudio, and aubio.

---

## ✅ Prerequisites

1. A **Home Assistant** server (local or remote)
2. **Python 3.12+** installed on your system

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/music-sync-lights.git
cd music-sync-lights
```

### 2. Install Dependencies

```bash
pip install requests pyaudio aubio numpy matplotlib
```

> 💡 If you're capturing system audio, you may need [VB-Audio Voicemeeter](https://vb-audio.com/Voicemeeter/) to create a virtual loopback input. See [Audio Routing Tips](#-audio-routing-tips) below.

---

## 🔧 Configuration

### 🔐 Getting Your Long-Lived Access Token

To control your lights via the Home Assistant API, you need a **Long-Lived Access Token**.

1. Log in to Home Assistant in your browser.
2. Click on your **user profile icon** in the bottom-left corner (usually your initials).
3. Scroll down to the **"Long-Lived Access Tokens"** section.
4. Click **"Create Token"**.
5. Enter a name like `Music Sync Lights` and click **OK**.
6. **Copy the token immediately** — it won’t be shown again!

Then paste the token into your script:

```python
TOKEN = "your_long_lived_access_token_here"
```

> 🔒 **Keep this token private!** Anyone with this token can control your Home Assistant devices.

---

### 🔧 Edit `MusicSync2.py` to Match Your Setup

```python
HOME_ASSISTANT_URL = "http://<your-home-assistant>:8123"
TOKEN = "your_long_lived_access_token"
LIGHT_IDS = ["light.lamp", "light.wiz"]  # Home Assistant light entities
AUDIO_DEVICE_INDEX = 60  # Found using input_device_index.py
LIGHT_LATENCY_DELAY = 0.1  # Tweak this if using Voicemeeter or networked audio
```

---

### 🎚 Find the Correct Audio Input Device Index

Run this helper script to list available audio input devices:

```bash
python input_device_index.py
```

Look for the name of your desired input (e.g., "Stereo Mix" or "Voicemeeter Input") and note the corresponding index number.

---

### 🎛 Verify That Audio Is Being Captured

Use the following command to check your input signal visually:

```bash
python Audio_Check.py
```

This displays a real-time frequency spectrum and dB meter for left/right channels.

---

## 🔊 Audio Routing Tips

To detect music playing through your speakers, you’ll need to route audio input back into Python.

### Option 1: Stereo Mix / Loopback (Built-in)

- Some audio drivers provide a "Stereo Mix" input.
- Run `input_device_index.py` and look for something like `"Stereo Mix"`.
- Set `AUDIO_DEVICE_INDEX` accordingly.

### Option 2: VB-Audio Voicemeeter (Recommended for Advanced Routing)

- Use Voicemeeter to split audio between physical outputs and a virtual input.
- Allows simultaneous playback and analysis.
- Slight delay (~100–300 ms) is expected.

To compensate, increase the latency delay in the script:

```python
LIGHT_LATENCY_DELAY = 0.25
```

> Tune this value until the lights feel synced with the music.

---

## ▶️ Run It

Once configured, start the script:

```bash
python MusicSync2.py
```

> 🎧 Lights will pulse to detected beats, flash on energetic sounds, and occasionally super-flash when both events occur simultaneously.

---

## 🎨 Customize

- 🎨 Modify the `COLOR_PALETTE` array to change available light colors.
- ⏱ Adjust `BEATS_PER_COLOR` to control how quickly colors cycle.
- 💡 Tweak brightness and transition values for more or less intense effects.

---

## 🧠 How It Works

- **Beat Detection**: Uses `aubio.onset` on bandpassed mono audio
- **Energy Detection**: Detects volume surges (e.g., drums, vocals)
- **Light Effects**:
  - **Pulse**: Colorful light burst on every beat
  - **Bass Flash**: White flash with cooldown
  - **Super Flash**: Max brightness when beat and energy overlap

---

## 📷 Demo

*(Insert a link to a YouTube short or GIF preview here)*

---

## 🧪 Tested On

- ✅ Windows 11 with VB-Audio Voicemeeter
- ✅ Home Assistant Supervised on Debian
- ✅ Philips Wiz, Cree RGB, and other RGBWW smart lights

---

## 📝 License

MIT License. Contributions and forks are welcome!