

from PyQt5.QtWidgets import QWidget, QMainWindow, QLabel, QApplication, QVBoxLayout, QHBoxLayout, QSlider
from PyQt5.QtGui import QPainter, QColor, QPixmap, QImage, QFont
from PyQt5.QtCore import Qt, QSize, QTimer

from Display import Display

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
    def __init__(self, port = 0):
        super(MainWindow, self).__init__()
        self.setStyleSheet("background-color: #1C1D1D;")  
        self.setWindowTitle("VISNUM Wheel Platonov")

        self.capture = cv2.VideoCapture(port)

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(1000./24)

        left = 320
        top = 70
        width = 1300
        height = 900

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
        self.last_direction_right = True
        self.t = list(range(self.NB_SHOWN)) 

    def process_frame(self):

        _, frame = self.capture.read()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        flipped = cv2.flip(rgb, 1)

        normal = cv2.resize(flipped, self.big_display_dims, interpolation=cv2.INTER_LINEAR)

        smaller = cv2.resize(normal, self.small_display_dims, interpolation=cv2.INTER_LINEAR)

        hsv_small = cv2.cvtColor(smaller, cv2.COLOR_RGB2HSV)
        

        left_min = np.array([self.parameters["hue min 1"], self.parameters["sat min 1"], self.parameters["val min 1"]])
        left_max = np.array([self.parameters["hue max 1"], self.parameters["sat max 1"], self.parameters["val max 1"]])
        right_min = np.array([self.parameters["hue min 2"], self.parameters["sat min 2"], self.parameters["val min 2"]])
        right_max = np.array([self.parameters["hue max 2"], self.parameters["sat max 2"], self.parameters["val max 2"]])

        left_mask = cv2.inRange(hsv_small, left_min, left_max)
        right_mask = cv2.inRange(hsv_small, right_min, right_max)

        left = cv2.bitwise_and(smaller,smaller, mask=left_mask)
        right = cv2.bitwise_and(smaller,smaller, mask=right_mask)

        bigger_left = cv2.resize(left, self.big_display_dims, interpolation=cv2.INTER_LINEAR)
        bigger_right = cv2.resize(right, self.big_display_dims, interpolation=cv2.INTER_LINEAR)

        # TEST
        line_thickness = 2

        lx, ly = self.get_shape_coord(bigger_left)
        rx, ry = self.get_shape_coord(bigger_right)

        is_left_locked = lx != None and ly != None
        is_right_locked = rx != None and ry != None

        # if is_left_locked:
        #     cv2.line(left, (0, ly), (lx, ly), (0,255,0), line_thickness)
        #     cv2.line(left, (lx, 0), (lx, ly), (0,255,0), line_thickness)
        
        # if is_right_locked:
        #     cv2.line(right, (0, ry), (rx, ry), (255,0,0), line_thickness)
        #     cv2.line(right, (rx, 0), (rx, ry), (255,0,0), line_thickness)
        
        if is_left_locked and is_right_locked:
            line_thickness = 2

            cv2.putText(bigger_left, "locked", (50, 70), cv2.FONT_HERSHEY_PLAIN, 4, (0,255,0), 2)

            cx, cy, theta = self.get_angle(lx, ly, rx, ry)

            cv2.line(bigger_left, (lx, ly), (rx, ry), (0,0,255), line_thickness)

            cv2.circle(bigger_left, (cx, cy), 5, (0,0,255), line_thickness)

        else: 
            theta = 0.0

            
        both = cv2.bitwise_or(bigger_left, bigger_right)


        self.build_plot(theta)

        self.angle_canvas.draw()

        self.feed_display.render(normal)

        self.object_both_display.render(both)

        self.object_1_display.render(left)

        self.object_2_display.render(right)


    def get_angle(self, lx, ly, rx, ry):

        rel_x = rx - lx
        rel_y = ry - ly

        length = int(math.sqrt(rel_x**2 + rel_y**2))

        center_x = rx - (rel_x//2) 
        center_y = ry - (rel_y//2)

        quadrants = [
            (rel_x >= 0 and rel_y < 0),
            (rel_x < 0 and rel_y < 0),
            (rel_x < 0 and rel_y >= 0),
            (rel_x >= 0 and rel_y >= 0)
        ]

        theta = math.degrees(math.asin(rel_y/length))
        # theta = -(360.0 - theta) if self.last_direction_right else theta

        # if quadrants[0]:
        #     if 
        # elif quadrants[1]:
        #     theta = -(360.0 - theta) if self.last_direction_right else theta
        # elif quadrants[2]:
        #     theta = -(360.0 - theta) if self.last_direction_right else theta
        # else:
        #     theta = -(360.0 - theta) if self.last_direction_right else theta

        # self.last_direction_right = not ()


        return center_x, center_y, theta

    def get_shape_coord(self, rgb_img):
        grayscale = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
        strel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
        opened = cv2.morphologyEx(grayscale, cv2.MORPH_OPEN, strel, iterations=2)

        num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(opened, 4, cv2.CV_32S)
        if 1 < num_labels < 20:

            areas = stats[:,4]
            sorted_coordinates = sorted(zip(areas, centroids), key = lambda x: x[0])

            main_centroid = sorted_coordinates[-2][1]
            
            if not any([math.isnan(main_centroid[0]), math.isnan(main_centroid[1])]):

                center_x = int(main_centroid[0])
                center_y = int(main_centroid[1])

                return center_x, center_y
        
        return None, None
    
    def build_plot(self, theta):

        # value = random.randint(0, 10)
        # value = random.randint(0, 10)
        self.angles.append(theta)
        self.t.append(len(self.angles))
        
        self.ax.clear()
        self.ax.plot(self.t[-1*self.NB_SHOWN:], self.angles[-1*self.NB_SHOWN:], '-')
        for tick in self.ax.get_xticklabels():
            tick.set_rotation(45)


    def init_UIElements(self):
        """ UI elements are initialized here, as well as their initial states """
        self.label_dims = (50, 30)
        self.slider_dims = (250, 30)
        self.big_display_dims = (640, 480)
        scaling_factor = 0.5
        self.small_display_dims = tuple([int(dim * scaling_factor) for dim in self.big_display_dims])

        self.letterColor = "cornflowerblue"

        self.feed_display = Display(*self.big_display_dims)
        self.angle_display = Display(*self.big_display_dims)
        self.object_both_display = Display(*self.big_display_dims)
        self.object_1_display = Display(*self.small_display_dims)
        self.object_2_display = Display(*self.small_display_dims)

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
        grad = """QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF0000, stop:0.2 #fff200 stop:0.4 #00FF00, stop:0.6 #00ffeb stop:0.8 #0000FF, stop:1 #ff00f2);
            }
            QSlider::add-page:horizontal {
                background: lightgray;
                }
            """
        # self.sliders[0].setStyleSheet(grad)
        # self.sliders[0].setStyleSheet(grad)
#             """QSlider::groove:horizontal {
#     border: 1px solid red;
#     height: 6px;
#     margin: 2px 0;
# border-radius: 3px;
# }
# QSlider::handle:horizontal {
#     background: red;
#     border: 1px solid red;
#     width: 3px;
#     margin: -8px 0;
#     border-radius: 1px;
# }
# QSlider::add-page:horizontal {
#     background: lightgray;
# }
# QSlider::sub-page:horizontal {
#     background: red;
# }""") 

        self.figure = plt.figure(figsize=(10,5))
        self.ax = self.figure.add_subplot(111)

        self.angle_canvas = FigureCanvas(self.figure)


    def build_slider(self, current, max_val):
        slider = QSlider(Qt.Horizontal, self)
        slider.setFixedSize(QSize(*self.slider_dims))
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setMinimum(0)
        slider.setMaximum(max_val)
        slider.setValue(current)
        slider.valueChanged.connect(self.update_from_parameters)
        slider.update
        return slider   

    def build_label(self, name):
        label = QLabel()
        label.setText(name)
        label.setFixedSize(*self.label_dims)
        label.setStyleSheet("QLabel {color: #858585};")
        return label

    def update_from_parameters(self):
        for key, slider in zip(self.parameters.keys(), self.sliders):
            self.parameters[key] = slider.value()

        self.started = True

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


