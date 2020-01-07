import ivport_nano as ivport
import cv2
import os


def gstreamer_pipeline(
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=30,
    flip_method=0,
):
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


def capture(camera,flip_method=0):
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=flip_method), cv2.CAP_GSTREAMER)
    if cap.isOpened():
        ret_val, img = cap.read()
        cv2.imwrite("still_CAM%d.jpg" % camera + '.jpg', img)
        cap.release()
    else:
        print("Unable to open camera")

iv = ivport.IVPort(ivport.TYPE_QUAD2,iv_jumper='A')
#iv.camera_open(camera_v2=True, resolution=(640, 480))

iv.camera_change(1)
capture(1,flip_method=2)
iv.camera_change(2)
capture(2,flip_method=2)
iv.camera_change(3)
capture(3)
iv.camera_change(4)
capture(4,flip_method=2)
iv.close()
