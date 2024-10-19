import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import numpy as np
import serial
import re
import time

class ECGWindow(QMainWindow):
    def _init_(self, serial_port):
        super()._init_()

        self.serial_port = serial_port
        self.initUI()
        self.initSerial()

    def initUI(self):
        self.setWindowTitle("Real-Time ECG Signal with PQRST Waves")
        self.setGeometry(100, 100, 1200, 800)  # Larger window for a wider x-axis

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)

        self.plot = self.plot_widget.plot(pen='g')
        self.plot_widget.setYRange(-60, 60)  # Amplified range for better visibility
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.setLimits(xMin=0, xMax=60)  # Limit x-axis from 0 to 60
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(1000)  # Update every 1000 ms (1 second)
        
        self.BPM = 70  # Default BPM
        self.sampling_rate = 500  # Sampling rate
        self.duration = 2  # Duration for each segment of signal
        self.total_time = 0
        self.max_duration = 60  # Max duration for x-axis
        self.time_data = np.linspace(0, self.duration, int(self.sampling_rate * self.duration))
        self.signal_data = np.zeros(int(self.sampling_rate * self.max_duration))  # Placeholder for ECG signal data
        self.gap_duration = 0.2  # Duration of gap in seconds
        self.gap_samples = int(self.sampling_rate * self.gap_duration)  # Number of samples in gap

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
        ecg_signal = np.tile(ecg_signal, int(np.ceil(self.duration * self.sampling_rate / len(ecg_signal))))[:int(self.sampling_rate * self.duration)]

        if self.total_time >= self.max_duration:
            self.signal_data = np.zeros(int(self.sampling_rate * self.max_duration))  # Clear the signal data
            self.total_time = 0

        # Insert gaps
        extended_signal = np.concatenate((ecg_signal, np.zeros(self.gap_samples)))
        self.signal_data = np.roll(self.signal_data, -len(extended_signal))
        self.signal_data[-len(extended_signal):] = extended_signal

        # Extend the time data
        self.time_data = np.linspace(0, self.max_duration, int(self.sampling_rate * self.max_duration))

        self.total_time += self.duration + self.gap_duration

        self.plot.setData(self.time_data, self.signal_data)
        self.plot_widget.setXRange(0, self.max_duration)

    def closeEvent(self, event):
        if self.ser:
            self.ser.close()
        event.accept()

if __name__ == '_main_':
    app = QApplication(sys.argv)
    serial_port = 'COM3'  # Adjust this to your actual serial port
    ex = ECGWindow(serial_port)
    ex.show()
    sys.exit(app.exec_())