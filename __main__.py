
import sys
import argparse
import cv2
import time
import numpy as np

from MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication


def parse_input():
    """ Argument parser. Returns a boolean indicator whether the feed should be a webcam stream """

    parser = argparse.ArgumentParser(description="Use a video as a racing wheel!")
    parser.add_argument('-l', '--live', default=False, action='store_true', help='use the program live on the webcam feed')
    args = parser.parse_args()
    return args.live


if __name__ == "__main__":
    is_live = parse_input()


    app = QApplication(sys.argv)
    window = MainWindow(is_live = is_live)
    window.show()
    sys.exit(app.exec_())
