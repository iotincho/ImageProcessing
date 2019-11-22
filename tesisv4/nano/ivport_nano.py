#!/usr/bin/env python

import sys
sys.path.append('/opt/nvidia/jetson-gpio/lib/python')
sys.path.append('/opt/nvidia/jetson-gpio/lib/python/Jetson/GPIO')

try:
    import IIC #TODO instalar smbus con pip, y deberia funcionar .ademas ver otros paquetes de apt aca https://github.com/juanmed/nano_gpio
    import RPi.GPIO as gp #TODO probar esto https://github.com/NVIDIA-AI-IOT/jetbot/issues/18 -> aparentemente funciona, hay que hacer la parte de permisos para poder importarlo
    gp.setwarnings(False)
    gp.setmode(gp.BOARD)
except:
    print "There are no IIC.py and RPi.GPIO module."
    print "install RPi.GPIO: sudo apt-get install python-rpi.gpio"
    sys.exit(0)

try:
    import camera
#    import picamera
#    import picamera.array
except:
    print 'camera module error'
#    print "There are no picamera module or directory."
    sys.exit(0)

TYPE_QUAD = 0
TYPE_QUAD2 = 1
TYPE_DUAL = 2
TYPE_DUAL2 = 3

class IVPort():
    IVJP = {'A': (11, 12), 'C': (21, 22), 'B': (15, 16), 'D': (23, 24)}
    pins = list(reduce(lambda x,y: x+y, IVJP.values()))
    pins.sort()
    DIVJP = {i+1 : x for i,x in enumerate(pins)}
    del(pins)

    def __init__(self, iv_type=TYPE_DUAL2, iv_jumper=1):

        self.fPin = self.f1Pin = self.f2Pin = self.ePin = 0
        self.ivport_type = iv_type
        self.is_camera_v2 = self.ivport_type in (TYPE_DUAL2, TYPE_QUAD2)
        self.is_dual = self.ivport_type in (TYPE_DUAL2, TYPE_DUAL)
        self.ivport_jumper = iv_jumper
        if not self.is_dual: self.ivport_jumper = 'A'
        self.camera = 1
        self.is_opened = False

        if self.is_camera_v2:
            self.iviic = IIC.IIC(addr=(0x70), bus_enable =(0x01))

        self.link_gpio()

    def link_gpio(self):
        if self.is_dual:
            self.fPin = self.DIVJP[self.ivport_jumper]
            gp.setup(self.fPin, gp.OUT)
        else:
            self.f1Pin, self.f2Pin = self.IVJP[self.ivport_jumper]
            self.ePin = 7
            gp.setup(self.f1Pin, gp.OUT)
            gp.setup(self.f2Pin, gp.OUT)
            gp.setup(self.ePin, gp.OUT)

    # ivport camera change
    def camera_change(self, camera=1):
        if self.is_dual:
            if camera == 1:
                if self.is_camera_v2: self.iviic.write_control_register((0x01))
                gp.output(self.fPin, False)
            elif camera == 2:
                if self.is_camera_v2: self.iviic.write_control_register((0x02))
                gp.output(self.fPin, True)
            else:
                print "Ivport type is DUAL."
                print "There isnt camera: %d" % camera
                self.close()
                sys.exit(0)
        else:
            if camera == 1:
                if self.is_camera_v2: self.iviic.write_control_register((0x01))
                gp.output(self.ePin, False)
                gp.output(self.f1Pin, False)
                gp.output(self.f2Pin, True)
            elif camera == 2:
                if self.is_camera_v2: self.iviic.write_control_register((0x02))
                gp.output(self.ePin, True)
                gp.output(self.f1Pin, False)
                gp.output(self.f2Pin, True)
            elif camera == 3:
                if self.is_camera_v2: self.iviic.write_control_register((0x04))
                gp.output(self.ePin, False)
                gp.output(self.f1Pin, True)
                gp.output(self.f2Pin, False)
#                self.picam.rotation = 180

            elif camera == 4:
#                self.picam.rotation = 0
                if self.is_camera_v2: self.iviic.write_control_register((0x08))
                gp.output(self.ePin, True)
                gp.output(self.f1Pin, True)
                gp.output(self.f2Pin, False)
            else:
                print "Ivport type is QUAD."
                print "Cluster feature hasnt been implemented yet."
                print "There isnt camera: %d" % camera
                self.close()
                sys.exit(0)
        self.camera = camera

    # picamera initialize
    # Camera V2
    # capture_sequence and start_recording require "camera_v2=True"
    # standart capture function doesnt require "camera_v2=True"
    def camera_open(self, camera_v2=False, resolution=(1280,720), framerate=1, grayscale=False):
        if self.is_opened: return
        self.picam = camera.Camera(resolution=resolution, framerate=framerate)
#        if grayscale: self.picam.color_effects = (128, 128)
        self.is_opened = True

    # picamera capture
    def camera_capture(self, filename, **options):
        if self.is_opened:
            self.picam.capture(filename + "_CAM" + str(self.camera) + '.jpg', **options)
        else:
            print "Camera is not opened."

    def get_frame(self, **options):
        if self.is_opened:
            return self.picam.camera_get_capture()
        else:
            print "Camera is not opened."
#    def camera_sequence(self, **options):
#        if self.is_opened:
#            self.picam.capture_sequence(**options)
#        else:
#            print "Camera is not opened."

    def close(self):
        self.camera_change(1)
        if self.is_opened: self.picam.close()
