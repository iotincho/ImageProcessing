
import cv2
import sys
import select
import argparse
# gstreamer_pipeline returns a GStreamer pipeline for capturing from the CSI camera
# Defaults to 1280x720 @ 60fps
# Flip the image by setting the flip_method (most common values: 0 and 2)
# display_width and display_height determine the size of the window on the screen


def gstreamer_pipeline(
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=1,
    flip_method=0):
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

class Camera:
    def __init__(self,
                resolution=(1280, 720),
                display_width=1280,
                display_height=720,
                framerate=1,
                flip_method=0):
        self._pipe_cmd = gstreamer_pipeline(capture_width=resolution[0],
                                            capture_height=resolution[1],
                                            display_width=display_width,
                                            display_height=display_height,
                                            framerate=framerate,
                                            flip_method=flip_method)
        self._capturer = cv2.VideoCapture(self._pipe_cmd, cv2.CAP_GSTREAMER)


    def capture(self,filename,**options):
        if self._capturer.isOpened():
            ret_val, img = self._capturer.read()
            cv2.imwrite(filename + '.jpg', img)

    def camera_get_capture(self,**options):
        if self._capturer.isOpened():
            ret_val, img = self._capturer.read()
            return img
        else:
            raise Exception('Camera not opened')
    def close(self):
        if self._capturer.isOpened():
            self._capturer.release()

