import cv2
import numpy as np
import time

t0 = time.time()
for i in range(100):
    t00 = time.time()
    frame = np.zeros((1920, 1080, 3), dtype = "uint8")
    t01 = time.time()
    frame = cv2.resize(frame, (960, 540), 0, 0, cv2.INTER_LINEAR)
    t02 = time.time()
    print(f"{t01 - t00} {t02 - t01}")
t1 = time.time()
print((t1 - t0) / 100)