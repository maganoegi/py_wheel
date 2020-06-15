

from PyQt5.QtWidgets import QWidget, QMainWindow, QLabel, QApplication, QVBoxLayout, QHBoxLayout, QSlider
from PyQt5.QtGui import QPainter, QColor, QPixmap, QImage, QFont
from PyQt5.QtCore import Qt, QSize, QTimer

from Display import Display

from lib import *

import sys
import time
import math

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

import random

class MainWindow(QMainWindow):
    def __init__(self, is_live):
        super(MainWindow, self).__init__()
        self.setStyleSheet("background-color: #1C1D1D;")  
        self.setWindowTitle("VISNUM Wheel Platonov")
        self.video_name = 'wheel_racing.avi'

        self.is_live = is_live
        self.frame_count = 0
        self.total_frame_count = None

        if is_live:
            V_PORT = 0
            self.capture = cv2.VideoCapture(V_PORT)
        else:
            self.capture = cv2.VideoCapture(self.video_name)
            self.total_frame_count = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(1000./24)

        left, top, width, height = 320, 70, 1300, 900

        self.setGeometry(left, top, width, height)
        self.setFixedSize(width, height)

        self.init_UIElements()
        self.init_Layouts()

        self.parameters = {}
        for i in range(2):
            for index, name in enumerate(self.slider_names):
                self.parameters[f"{name} {i + 1}"]  = self.slider_default_max[index][index%2]
       
        self.NB_SHOWN = 100
        self.angles = [0] * self.NB_SHOWN
        self.t = list(range(self.NB_SHOWN))
        self.started = False

    def get_frame(self):
        ret, frame = self.capture.read()

        if not self.is_live:
            self.frame_count += 1

            if not ret:
                # if an error occured while reading, reset the capture
                # NOTE: cap.set(cv2.CV_CAP_PROP_POS_FRAMES, 0) did not work on my machine - this ensures it will work 

                # save the angles recorded thus far to a file
                angle_string = ";".join(self.angles)
                with open("angles.txt", "w") as f:
                    f.write(angle_string)

                self.capture.release()
                self.capture = cv2.VideoCapture(self.video_name)
                self.frame_count = 1

                _, frame = self.capture.read()

        return frame


    def process_frame(self):
        """
        Process the current frame and update the necessary views.
        """

        # extract the frame to be processed. The error-handling is included
        frame = self.get_frame()

        # convert the frame at hand to RGB, since we are using matplotlib for displaying the results
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # flip the image along its vertical axis
        flipped = cv2.flip(rgb, 1)

        # normalize our input image to 2 formats: bigger and smaller. This because our UI contains screens of 2 sizes.
        bigger = cv2.resize(flipped, self.DSPLY_DIM_BIG, interpolation=cv2.INTER_LINEAR)
        smaller = cv2.resize(flipped, self.DSPLY_DIM_SMALL, interpolation=cv2.INTER_LINEAR)

        # make a copy of a "smaller" image expressed in HSV color format
        hsv_small = cv2.cvtColor(smaller, cv2.COLOR_RGB2HSV)

        # process the smaller HSV image with respect to logic for the image on the left and on the right. The difference is which HSV value range masks are applied.
        # this creates 2 images, left and right, preparing it for being displayed.
        left = hsv_transform(
                    is_left=True, 
                    img=smaller,
                    hsv_img=hsv_small,
                    parameters=self.parameters)


        right = hsv_transform(
                    is_left=False, 
                    img=smaller,
                    hsv_img=hsv_small,
                    parameters=self.parameters)


        # resize the left and right images for analysis, merging and displaying on a bigger screen
        bigL = cv2.resize(left, self.DSPLY_DIM_BIG, interpolation=cv2.INTER_LINEAR)
        bigR = cv2.resize(right, self.DSPLY_DIM_BIG, interpolation=cv2.INTER_LINEAR)

        # combine the center window, containing the merged smaller windows and subsequent analysis
        LR_combined, theta = analyze_detection(bigL, bigR, self.started)

        # draw the display contents for this frame
        self.update_view(theta, bigger, LR_combined, left, right)


    def update_view(self, theta, bigger, LR_combined, left, right):
        self.build_plot(theta)
        self.angle_canvas.draw()
        self.feed_display.render(bigger)
        self.object_both_display.render(LR_combined)
        self.object_1_display.render(left)
        self.object_2_display.render(right)

    
    def build_plot(self, theta):
        """ handles the angle plot logic: the data we actually display, and the way we present it """
        self.angles.append(theta)
        self.t.append(len(self.angles))
        
        self.ax.clear()
        self.ax.plot(self.t[-1*self.NB_SHOWN:], self.angles[-1*self.NB_SHOWN:], '-')
        for tick in self.ax.get_xticklabels():
            tick.set_rotation(45)


    def init_UIElements(self):
        """ UI elements are initialized here, as well as their initial states """
        self.LBL_DIM = (50, 30)
        self.SLIDER_DIM = (250, 30)
        self.DSPLY_DIM_BIG = (640, 480)
        scaling_factor = 0.5
        self.DSPLY_DIM_SMALL = tuple([int(dim * scaling_factor) for dim in self.DSPLY_DIM_BIG])

        self.letterColor = "cornflowerblue"

        self.feed_display = Display(*self.DSPLY_DIM_BIG)
        self.object_both_display = Display(*self.DSPLY_DIM_BIG)
        self.object_1_display = Display(*self.DSPLY_DIM_SMALL)
        self.object_2_display = Display(*self.DSPLY_DIM_SMALL)

        # This part of the code might seem confusing, and it is... 
        # my goal was to experiment with dictionary and list comprehensions to provide a more dynamic initialization and reading. 
        # It is written around a format that I defined for my "parameters"/HSV slider values. Then, I exploited the patterns I spotted in this format to initialize the thing.
        self.slider_names = [
            "hue min",
            "hue max",
            "val min",
            "val max",
            "sat min",
            "sat max"
        ]

        self.slider_default_max = [
            (0, 255),
            (255, 255),
            (0, 255),
            (255, 255),
            (0, 255),
            (255, 255)
        ]

        self.slider_labels = [self.build_label(name) for name in (self.slider_names + self.slider_names)]
        self.sliders = [self.build_slider(*current_max) for current_max in (self.slider_default_max + self.slider_default_max)]
        self.figure = plt.figure(figsize=(10,5))
        self.ax = self.figure.add_subplot(111)

        self.angle_canvas = FigureCanvas(self.figure)


    def build_slider(self, current, max_val):
        """ builds sliders with a specified, uniform format """
        slider = QSlider(Qt.Horizontal, self)
        slider.setFixedSize(QSize(*self.SLIDER_DIM))
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setMinimum(0)
        slider.setMaximum(max_val)
        slider.setValue(current)
        slider.valueChanged.connect(self.update_parameters)
        slider.update
        return slider   

    def build_label(self, name):
        """ builds labels with a specified, uniform format """
        label = QLabel()
        label.setText(name)
        label.setFixedSize(*self.LBL_DIM)
        label.setStyleSheet("QLabel {color: #858585};")
        return label

    def update_parameters(self):
        """ 
        Updates the HSV parameters depending on the corresponding slider values. 
        This is triggered on value update. 
        The parameters are read in image processing.
        """
        self.started = True
        for key, slider in zip(self.parameters.keys(), self.sliders):
            self.parameters[key] = slider.value()

    def init_Layouts(self):
        """ layouts are initialized here, as well as their contents """
        self.w = QWidget()

        # Define containers...

        self.main_container = QVBoxLayout()
        
        self.upper_container = QHBoxLayout()

        self.lower_container = QHBoxLayout()

        self.object_1_container = QVBoxLayout()

        self.object_1_N = QVBoxLayout()
        
        self.object_1_S = QHBoxLayout()

        self.object_1_SW = QVBoxLayout()

        self.object_1_SE = QVBoxLayout()

        self.object_2_container = QVBoxLayout()

        self.object_2_N = QVBoxLayout()
        
        self.object_2_S = QHBoxLayout()

        self.object_2_SW = QVBoxLayout()

        self.object_2_SE = QVBoxLayout()

        self.object_both_container = QVBoxLayout()

        # ... fill them with widgets ...

        self.upper_container.addWidget(self.feed_display)
        self.upper_container.addWidget(self.angle_canvas)

        self.object_1_N.addWidget(self.object_1_display)
        for slider, label in zip(self.sliders[:6], self.slider_labels[:6]):
            self.object_1_SW.addWidget(slider)
            self.object_1_SE.addWidget(label)

        self.object_2_N.addWidget(self.object_2_display)
        for slider, label in zip(self.sliders[6:], self.slider_labels[6:]):
            self.object_2_SW.addWidget(slider)
            self.object_2_SE.addWidget(label)

        self.object_both_container.addWidget(self.object_both_display)

        # ... and combine the containers
        
        self.setCentralWidget(self.w)
        self.w.setLayout(self.main_container)

        self.main_container.addLayout(self.upper_container)
        self.main_container.addLayout(self.lower_container)

        self.lower_container.addLayout(self.object_1_container)
        self.lower_container.addLayout(self.object_both_container)
        self.lower_container.addLayout(self.object_2_container)

        self.object_1_container.addLayout(self.object_1_N)
        self.object_1_container.addLayout(self.object_1_S)

        self.object_1_S.addLayout(self.object_1_SW)
        self.object_1_S.addLayout(self.object_1_SE)

        self.object_2_container.addLayout(self.object_2_N)
        self.object_2_container.addLayout(self.object_2_S)

        self.object_2_S.addLayout(self.object_2_SW)
        self.object_2_S.addLayout(self.object_2_SE)


