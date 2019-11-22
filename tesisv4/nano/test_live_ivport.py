import ivport_nano as ivport
import cv2
import os
from threading import Thread

def gstreamer_pipeline(
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=30,
    flip_method=0,):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def capture(camera,cap):
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=2,framerate=0.25), cv2.CAP_GSTREAMER)
    if cap.isOpened():
        ret_val, img = cap.read()
	if ret_val:
		cv2.imshow('im',img)
        #cv2.imwrite("still_CAM%d.jpg" % camera + '.jpg', img)
        #cap.release()
    else:
        print("Unable to open camera")


iv = ivport.IVPort(ivport.TYPE_QUAD2,iv_jumper='A')

#iv.camera_open(camera_v2=True,framerate=10)

for camera in range(1,4):
    iv.camera_change(camera)
    for i in range(0,10):
        capture(1,None)
        #im = iv.get_frame()
        #cv2.imshow('im',im)
        cv2.waitKey(1)


iv.close()


