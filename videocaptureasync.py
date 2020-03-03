# file: videocaptureasync.py
import threading
import cv2
from time import sleep
import copy

class VideoCaptureAsync:
    def __init__(self, width=1920, height=1080, thermal=True):
        self.src = '20200130_154806A_Trim_Trim.mp4'
        self.cap = cv2.VideoCapture(self.src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.grabbed, self.frame = self.cap.read()
        self.started = False
        self.read_lock = threading.Lock()

    def set(self, var1, var2):
        self.cap.set(var1, var2)

    def start(self):
        if self.started:
            print('[!] Asynchroneous video capturing has already been started.')
            return None
        self.started = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.start()
        return self

    def update(self):
        while self.started:
            sleep(0.03)
            grabbed, frame = self.cap.read()
            with self.read_lock:
                self.grabbed = grabbed
                self.frame = frame

    def read(self):
        with self.read_lock:
            frame = self.frame.copy()
            grabbed = self.grabbed
        return grabbed, frame

    def isOpened(self):
        return self.cap.isOpened()

    def stop(self):
        self.started = False
        self.thread.join()
    def release(self):
        self.cap.release()

    def __exit__(self, exec_type, exc_value, traceback):
        self.cap.release()