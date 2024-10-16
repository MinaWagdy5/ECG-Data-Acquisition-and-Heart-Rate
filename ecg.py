import matplotlib.pyplot as plt
import numpy as np
import serial
import time
import re


def generate_ecg_waveform(BPM, duration, sampling_rate):
    beat_duration = 60 / BPM
    t = np.linspace(0, duration, int(sampling_rate * duration))

    def p_wave(t):
        return 0.25 * np.sin(np.pi * t / 0.09) * (t < 0.09)

    def q_wave(t):
        return -0.1 * np.sin(np.pi * (t - 0.09) / 0.066) * ((t >= 0.09) & (t < 0.156))

    def r_wave(t):
        return 1.0 * np.sin(np.pi * (t - 0.156) / 0.1) * ((t >= 0.156) & (t < 0.256))

    def s_wave(t):
        return -0.25 * np.sin(np.pi * (t - 0.256) / 0.066) * ((t >= 0.256) & (t < 0.322))

    def t_wave(t):
        return 0.35 * np.sin(np.pi * (t - 0.36) / 0.142) * ((t >= 0.36) & (t < 0.502))

    heartbeat = p_wave(t % beat_duration) + q_wave(t % beat_duration) + r_wave(t %
                                                                               beat_duration) + s_wave(t % beat_duration) + t_wave(t % beat_duration)
    ecg_signal = np.tile(heartbeat, int(duration / beat_duration))
    return t, ecg_signal[:len(t)]


def read_serial_data(serial_port):
    ser = serial.Serial(serial_port, 9600)
    time.sleep(2)  # Wait for the connection to establish
    BPM = 50  # Default BPM value

    plt.ion()  # Turn on interactive mode for real-time updates
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=2)
    ax.set_ylim(-1.5, 1.5)  # Initial y-axis limit
    plt.title("Real-Time ECG Signal with PQRST Waves")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.grid()

    sampling_rate = 250
    duration = 7  # Duration in seconds for the rolling window

    while True:
        if ser.in_waiting > 0:
            line_data = ser.readline().decode().strip()
            # Extract the BPM value using regular expression
            match = re.search(r'\d+', line_data)
            if match:
                BPM = int(match.group())
                print(f"Received BPM: {BPM}")
                if BPM >= 60 and BPM <= 100:
                    print("regular heart beat")
                else:
                    print("Irregular heart beat")

        t, ecg_signal = generate_ecg_waveform(BPM, duration, sampling_rate)
        line.set_xdata(t)
        line.set_ydata(ecg_signal)
        ax.relim()
        # Rescale x-axis view to fit the data
        ax.autoscale_view(scalex=True, scaley=False)

        plt.draw()
        plt.pause(0.01)  # Pause to allow for real-time plotting

    ser.close()


# Parameters
serial_port = 'COM3'  # Adjust this to your actual serial port

# Read serial data and update ECG waveform
read_serial_data(serial_port)
