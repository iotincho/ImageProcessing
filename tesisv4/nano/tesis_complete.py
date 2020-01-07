#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import Queue
#from __future__ import print_function
import threading
import socket
import ivport_nano as ivport
import time
import sys
import argparse
import signal
from multiprocessing import Process,Event
from multiprocessing import JoinableQueue as Queue
from Queue import Empty as EmptyQueue
import cv2
import os
import numpy as np
from ctypes import *
import math
import random
import detector as dn
import datetime

path_capturas = 'imagenes/'
def gstreamer_pipeline(
    capture_width=640,
    capture_height=480,
    display_width=640,
    display_height=480,
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

class Captura:#(Process):
   def __init__(self, cola, args):
       #Process.__init__(self)
       self.cola = cola
       self.args = args
       self.shutdown_flag = threading.Event()

   def run(self):
       iv = ivport.IVPort(ivport.TYPE_QUAD2, iv_jumper='A')

       #iv.camera_open(camera_v2=True, resolution=(1024,768))
       i=0
       while not self.shutdown_flag.is_set(): #and cap.isOpened():
           sys.stdout.flush()
           if self.args.time:
                print ('[CAPTURA] Tomando tiempo')
                start = time.time()

           iv.camera_change(1)
           #iv.camera_capture(path_capturas+"picam", use_video_port=False)
           cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=2,framerate=30), cv2.CAP_GSTREAMER)
           ret_val, img = cap.read()
           cap.release()
           #cv2.imwrite(path_capturas+"picam_CAM1.jpg",img)
           if self.args.verbose:
               print ('[CAPTURA] Captura1!')
           self.cola.put(img)

           iv.camera_change(2)
           #iv.camera_capture(path_capturas+"picam", use_video_port=False)
           cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=2,framerate=30), cv2.CAP_GSTREAMER)
           ret_val, img = cap.read()
           cap.release()
           #cv2.imwrite(path_capturas+"picam_CAM2.jpg",img)
           if self.args.verbose:
               print ('[CAPTURA] Captura2!')
           self.cola.put(img)

           iv.camera_change(3)
           #iv.camera_capture(path_capturas+"picam", use_video_port=False)
           cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0,framerate=30), cv2.CAP_GSTREAMER)
           ret_val, img = cap.read()
           cap.release()
           #cv2.imwrite(path_capturas+"picam_CAM3.jpg",img)
           if self.args.verbose:
               print ('[CAPTURA] Captura3!')
           self.cola.put(img)


           iv.camera_change(4)
           #iv.camera_capture(path_capturas+"picam", use_video_port=False)
           cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=2,framerate=30), cv2.CAP_GSTREAMER)
           ret_val, img = cap.read()
           cap.release()
           #cv2.imwrite(path_capturas+"picam_CAM4.jpg",img)
           if self.args.verbose:
               print ('[CAPTURA] Captura4!')
           self.cola.put(img)

           self.cola.join()
           i += 1
           if self.args.time:
                    end = time.time()
                    print ('[CAPTURA] Tiempo:' ,end - start)


class Stit(Process):
    def __init__(self, cola, colaProce, finish_event,args):
        Process.__init__(self)
        self.cola = cola
        self.colaProce = colaProce
        self.args = args
        self.shutdown_flag = finish_event

    def run(self):
        try:
            i = 0
            print('[STITCHER] stither is alive')
            while not self.shutdown_flag.is_set():
                sys.stdout.flush()
                if self.args.time:
                    print('[STITCHER] Tomando tiempo')
    #                start = time.time()


                imagenes = []
                if self.args.verbose:
                    print('[STITCHER] Estoy en Stit')
                stitcher = cv2.Stitcher_create(mode=cv2.Stitcher_SCANS)#try_use_gpu=False)
                try:
                    imagenes.append(self.cola.get(timeout=30)); self.cola.task_done()
                    imagenes.append(self.cola.get(timeout=30)); self.cola.task_done()
                    imagenes.append(self.cola.get(timeout=30)); self.cola.task_done()
                    imagenes.append(self.cola.get(timeout=30)); self.cola.task_done()
                except EmptyQueue:
                    print("[STITCHER] EmptyQueue Error")
                    continue

                start = time.time()
                if imagenes is None:
                    print('[STITCHER] No se pudo leer imagen ')

                #if len(imagenes) > 4:
                #    imagenes = imagenes[0:3]
                status, pano = stitcher.stitch(imagenes)

                if status == 1:
                    print('[STITCHER] No se unieron, se necesitan mas imagenes. count: %d'%len(imagenes))
                    for imagen in imagenes:
                        print('[STITCHER] %s'%str(imagen.shape))
                        cv2.imwrite("%sim_%d.jpg"%(path_capturas,i),imagen)
                        i+=1
                elif status == 3:
                    print('[STITCHER] ERR_CAMERA_PARAMS_ADJUST_FAIL')
                else:
                    tiempo = time.time()
                    st = datetime.datetime.fromtimestamp(tiempo).strftime('%d-%m-%YY-%H:%M:%S')
                    nombre_archivo = path_capturas + 'stit' + st + '.jpg'
                    cv2.imwrite(nombre_archivo, pano);
                    if self.args.verbose:
                        print('[STITCHER] stitching correcto: ' + nombre_archivo)
                    self.colaProce.put(nombre_archivo)
                    if self.args.time:
                        end = time.time()
                        print('[STITCHER] Tiempo: ', end - start)

                    i += 1
        except ServiceExit:
            exit(0)

class Proce(Process):

    def __init__(self, colaProce,finish_event, args):
        Process.__init__(self)
        self.colaProce = colaProce
        self.args = args
        self.shutdown_flag = finish_event

    def run(self):
        try:

            i = 0
            if self.args.time:
                print("[PROCE] Tomando tiempo carga de pesos")
                start = time.time()
            net = dn.load_net("cfg/yolov3-tiny.cfg", "yolov3-tiny.weights", 0)
            meta = dn.load_meta("cfg/coco.data")
            dn.set_gpu(0)
            filtro = 0
            if self.args.time:
                end = time.time()
                print("[PROCE] Tiempo carga de pesos: ", end - start)
            if self.args.filtro:
                filtro = 1
            while not self.shutdown_flag.is_set():
                sys.stdout.flush()
                if self.args.time:
                    print("[PROCE] Tomando tiempo")
    #               start = time.time()
                try:
                    img = self.colaProce.get(timeout=30)
                except EmptyQueue:
                    continue
                start = time.time()
                r = dn.detect(filtro, i, self.args.show, net, meta, img)
                print("[PROCE] ", i, " ", r)
                if self.args.time:
                    end = time.time()
                    print("[PROCE] Tiempo: ", end - start)
                i += 1
        except ServiceExit:
            exit(0)




class ServiceExit(Exception):

    pass


def service_shutdown(signum, frame):
    print(' Se tomo signal %d' % signum)
    raise ServiceExit


def main():
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Mostrar información de depuración", action="store_true")
    parser.add_argument("-p", "--port" , type=int, help="Puerto a enviar")
    parser.add_argument("-ip", "--ip" , type=int, help="IP del receptor")
    parser.add_argument("-t", "--time" , action="store_true", help="Tomar tiempos")
    parser.add_argument("-s", "--show", help="Mostrar imagen final", action="store_true")
    parser.add_argument("-f", "--filtro", action="store_true", help="Filtrar detecciones +%80")

    args = parser.parse_args()
    # print (args)
    if args.verbose:
        print ("Depuración activada!!!")
    if args.time:
        print ("Tomando tiempos!!")
    if args.port:
        print ("Se seteo puerto!!")
    if args.ip:
        print ("Se seteo ip!!")
    if args.filtro:
        print("Filtrando detecciones!!")


    try:
        finish = Event()
        cola_stit  =  Queue()#Queue.Queue()
        cola_proce = Queue()
        captura    = Captura(cola_stit, args)
        stitcher   = Stit(cola_stit, cola_proce,finish, args)
        proce      = Proce(cola_proce,finish, args)

        proce.start()
        stitcher.start()
        time.sleep(5)
        captura.run()
        while True:
            time.sleep(0.5)

    except ServiceExit:
        print('finising')
        finish.set()
        # Wait for the threads to close...
        stitcher.join()
        proce.join()

        #captura.join()
        print('finished')

if __name__ == '__main__':
   main()
