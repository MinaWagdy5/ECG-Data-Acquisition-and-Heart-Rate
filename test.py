import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
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
        self.setGeometry(100, 100, 1200, 800)  

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.bpm_label = QLabel("BPM: 70") 
        self.regularity_label = QLabel("regular heart beat") 
        self.layout.addWidget(self.bpm_label)
        self.layout.addWidget(self.regularity_label)

        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)

        self.plot = self.plot_widget.plot(pen='g')
        self.plot_widget.setYRange(-3, 3)  

        self.x_start = 0
        self.x_end = 10
        
        self.plot_widget.setXRange(self.x_start, self.x_end)
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.setLimits(xMin=0, xMax=60)  
        self.plot_widget.hideAxis('bottom')
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(800)  
        
        self.BPM = 70  
        self.old_BPM = 70
        self.sampling_rate = 1000  
        self.duration = 2  
        self.total_time = 0
        self.max_duration = 20000  
        self.time_data = np.linspace(0, self.duration, int(self.sampling_rate * self.duration))
        self.signal_data = np.zeros(int(self.sampling_rate * self.max_duration))  
        self.gap_duration = 0.2  
        self.gap_samples = int(self.sampling_rate * self.gap_duration)  

    def initSerial(self):
        try:
            self.ser = serial.Serial(self.serial_port, 9600)
            time.sleep(2)  
        except Exception as e:
            print(f"Error opening serial port: {e}")
            self.ser = None

    def generate_ecg_waveform(self, BPM):
        if BPM == 0:
            return np.zeros(int(self.sampling_rate * self.duration))  

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
        return heartbeat   

    def update_plot(self):
        if self.ser and self.ser.in_waiting > 0:
            line_data = self.ser.readline().decode().strip()
            match = re.search(r'\d+', line_data)
            if match:
                self.BPM = int(match.group())
                self.bpm_label.setText(f"BPM: {self.BPM}") 
                if self.BPM >= 60 and self.BPM <= 100:
                    self.regularity_label.setText(f"regular heart beat") 
                else:
                    self.regularity_label.setText(f"Irregular heart beat") 
    
        if self.old_BPM != self.BPM:
            self.plot.clear()
            self.x_start = 0
            self.x_end = 10
            self.old_BPM = self.BPM

        ecg_signal = self.generate_ecg_waveform(self.BPM)
        

        if self.total_time >= self.max_duration:
            self.signal_data = np.zeros(int(self.sampling_rate * self.max_duration))  
            self.total_time = 0

        
        extended_signal = np.concatenate((ecg_signal, np.zeros(self.gap_samples)))
        self.signal_data = np.roll(self.signal_data, len(extended_signal))
        self.signal_data[-len(extended_signal):] = extended_signal

        
        self.time_data = np.linspace(0, self.max_duration, int(self.sampling_rate * self.max_duration))

        self.total_time += self.duration + self.gap_duration

        self.plot.setData(self.time_data, self.signal_data)
        
        self.x_start += 0.6
        self.x_end += 0.6
        self.plot_widget.setXRange(self.x_start, self.x_end)

    def closeEvent(self, event):
        if self.ser:
            self.ser.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    serial_port = 'COM3'  
    ex = ECGWindow(serial_port)
    ex.show()
    sys.exit(app.exec_())
