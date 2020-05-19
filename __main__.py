
import sys
import argparse
import cv2
import time
import numpy as np

from MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication


def parse_input() -> (str, int, int, float, float, bool, bool):
    """ 
        argument parser wrapper. Terminal commands and parameters are defined here.
        * useful for this implementation, as it allows for easy parameter tuning for learning purposes
    """
    parser = argparse.ArgumentParser(description="Apply the Hough Transform on the target image")
    parser.add_argument('-l', '--live', default=False, action='store_true', help='use the program live on the webcam feed')
    args = parser.parse_args()

    return args.live


def wheel():
    pass
    # import sys
    # from Canvas import Canvas
    # from MainWindow import MainWindow
    # from PyQt5.QtWidgets import QApplication

    # if __name__ == "__main__":
    #     app = QApplication(sys.argv)
    #     window = MainWindow()
    #     window.show()
    #     sys.exit(app.exec_())

def feed_test():
    live = parse_input()

    # if not live:
    #     cap = cv2.VideoCapture('wheel_racing.avi') # video
    # else:
    #     cap = cv2.VideoCapture(0) # webcam

    while True:
        # _, frame = cap.read()

        # cv.SetCaptureProperty(camcapture,cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
        # cv.SetCaptureProperty(camcapture,cv.CV_CAP_PROP_FRAME_HEIGHT, 720);

        # frame = cv2.QueryFrame(camcapture)

        sharp_kernel = np.array([
            [-1,-1,-1],
            [-1, 8,-1],
            [-1,-1,-1]
        ], dtype='float64')


        # strel = cv2.getStructuringElement(cv2.MORPH_RECT, (50,1))

        # frame = cv2.morphologyEx(frame, cv2.MORPH_BLACKHAT, strel)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # frame = cv2.Sobel(frame, -1, 1, 1, ksize=5)
        # frame = cv2.filter2D(frame, -1, sharp_kernel)
        
        frame = cv2.Canny(frame, 50, 150)

        cv2.imshow('frame', frame)

        if not live: time.sleep(0.02)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
