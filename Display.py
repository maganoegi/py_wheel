
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QSize

import cv2


class Display(QLabel):
    def __init__(self, width, height):
        super().__init__()
        pixmap = QPixmap(width, height)
        self.setPixmap(pixmap)


    def render(self, frame):

        q_image = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)

        self.image = q_image

        self.setPixmap(QPixmap.fromImage(q_image))




