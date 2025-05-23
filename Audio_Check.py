import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import shutil
import os

# Settings
device_index = 66  # Set to your input device index
CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 2
RATE = 44100  # Can be adjusted or pulled from device

# Init PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK)

# Setup matplotlib
fig, ax = plt.subplots()
x = np.fft.rfftfreq(CHUNK, 1.0 / RATE)
line, = ax.plot(x, np.zeros_like(x))
ax.set_ylim(0, 50)
ax.set_xlim(20, RATE / 2)
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Magnitude")
plt.title("Live Frequency Spectrum (Averaged Stereo)")

def get_volume_bar(db, width=50):
    if db <= -80:
        db = -80
    if db >= 0:
        db = 0
    length = int((db + 80) / 80 * width)
    return "[" + "#" * length + "-" * (width - length) + f"] {db:.1f} dB"

def update(frame):
    data = stream.read(CHUNK, exception_on_overflow=False)
    samples = np.frombuffer(data, dtype=np.float32)
    samples = samples.reshape(-1, 2)  # Reshape for stereo (Left, Right)

    left = samples[:, 0]
    right = samples[:, 1]
    stereo_avg = (left + right) / 2.0

    # Compute RMS and dB for each channel
    def compute_db(channel_data):
        rms = np.sqrt(np.mean(channel_data**2))
        return 20 * np.log10(rms) if rms > 0 else -np.inf

    db_left = compute_db(left)
    db_right = compute_db(right)

    # FFT on averaged stereo
    fft = np.fft.rfft(stereo_avg)
    magnitude = np.abs(fft)
    freqs = np.fft.rfftfreq(len(stereo_avg), 1.0 / RATE)
    peak_freq = freqs[np.argmax(magnitude)]

    # Terminal output
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"Dominant Frequency: {peak_freq:.1f} Hz")
    print("Left :", get_volume_bar(db_left))
    print("Right:", get_volume_bar(db_right))

    # Update plot
    line.set_ydata(magnitude)
    return line,

ani = animation.FuncAnimation(fig, update, interval=50)
plt.show()

# Cleanup
stream.stop_stream()
stream.close()
p.terminate()
