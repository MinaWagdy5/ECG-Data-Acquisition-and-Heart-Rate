import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import numpy as np
import serial
import re
import time

class ECGWindow(QMainWindow):
    def __init__(self, serial_port):
        super().__init__()

        self.serial_port = serial_port
        self.initUI()
        self.initSerial()

    def initUI(self):
        self.setWindowTitle("Real-Time ECG Signal with PQRST Waves")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)

        self.plot = self.plot_widget.plot(pen='g')
        self.plot_widget.setYRange(-5, 5)  # Amplified range for better visibility
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)  # Update every 50 ms
        
        self.BPM = 70  # Default BPM
        self.sampling_rate = 100  # Lower sampling rate to smooth out the signal
        self.duration = 10  # Duration for each segment of signal
        self.time_data = np.arange(0, self.duration, 1/self.sampling_rate)
        self.signal_data = np.zeros(self.duration * self.sampling_rate)  # Placeholder for ECG signal data

    def initSerial(self):
        try:
            self.ser = serial.Serial(self.serial_port, 9600)
            time.sleep(2)  # Wait for the connection to establish
        except Exception as e:
            print(f"Error opening serial port: {e}")
            self.ser = None

    def generate_ecg_waveform(self, BPM):
        beat_duration = 60 / BPM
        t = np.linspace(0, beat_duration, int(self.sampling_rate * beat_duration))

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

        heartbeat = p_wave(t) + q_wave(t) + r_wave(t) + s_wave(t) + t_wave(t)
        return heartbeat * 5  # Amplify the signal significantly

    def update_plot(self):
        if self.ser and self.ser.in_waiting > 0:
            line_data = self.ser.readline().decode().strip()
            match = re.search(r'\d+', line_data)
            if match:
                self.BPM = int(match.group())
                print(f"Received BPM: {self.BPM}")

        ecg_signal = self.generate_ecg_waveform(self.BPM)
        ecg_signal = np.tile(ecg_signal, int(np.ceil(self.duration * self.sampling_rate / len(ecg_signal))))[:self.duration * self.sampling_rate]

        # Shift the signal data and append new data
        self.signal_data = np.roll(self.signal_data, -len(ecg_signal))
        self.signal_data[-len(ecg_signal):] = ecg_signal

        # Extend the time data
        self.time_data += self.duration

        self.plot.setData(self.time_data, self.signal_data)
        self.plot_widget.setXRange(self.time_data.min(), self.time_data.max())

    def closeEvent(self, event):
        if self.ser:
            self.ser.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    serial_port = 'COM3'  # Adjust this to your actual serial port
    ex = ECGWindow(serial_port)
    ex.show()
    sys.exit(app.exec_())
