import ivport_nano as ivport
import cv2
import os
from multiprocessing import Process, Queue
import time
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


def capture(queue):
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=2,framerate=10), cv2.CAP_GSTREAMER)
    while cap.isOpened():
        ret_val, img = cap.read()
#        with queue.mutex:
#        queue.clear()
        queue.put(img)
        #cv2.imshow('im',img)
        #cv2.imwrite("still_CAM%d.jpg" % camera + '.jpg', img)
        #cap.release()
    else:
        print("Unable to open camera")



if __name__=='__main__':
    iv = ivport.IVPort(ivport.TYPE_QUAD2,iv_jumper='A')
    iv.camera_change(1)
    queue = Queue()
    pr = Process(target=capture,args=(queue,))
    pr.start()
    time.sleep(1)
    for camera in range(1, 5):
        iv.camera_change(camera)
        for i in range(0,10):
	    while queue.empty():
		pass
#	    with queue.mutex:
            im = queue.get()        
            #im = iv.get_frame()
            cv2.imshow('im',im)
            cv2.waitKey(1)


    iv.close() 
