#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import Queue
import threading
import socket
import time
import os
import numpy as np
import cv2 as cv
import sys
from ctypes import *
import math
import random
import detector as dn
import argparse
import datetime
import struct
import pickle
import cv2

path_capturas = "imagenes/"

class Recep(threading.Thread):
    def __init__(self, cola, args):
        threading.Thread.__init__(self)
        self.cola = cola
        self.args = args

    def run(self):
        s = socket.socket()
        host = "0.0.0.0"
        port = 9996
        if self.args.port:
            port = self.args.port

        s.bind((host, port))
        s.listen(10)

        i = 1
        if self.args.verbose:
            print("[RECEP] Esperando conexion en puerto: " + str(port))

        payload_size = struct.calcsize(">L")
        while True:
            try:
                sc, address = s.accept()
            except Exception:
                break
            if self.args.verbose:
                print("[RECEP] Conexion con " + str(address))

            head = sc.recv(len('IMAGE'))
            if head == 'IMAGE':
                print("Receiving:")
                if self.args.time:
                    print("[RECEP] Tomando tiempo")
                    start = time.time()
                data = b''
                data += sc.recv(payload_size)
                while len(data) < payload_size:
                    # esto permite obtener el la info faltante por si no se recibio el dato completo
                    data += sc.recv(1)
                packed_msg_size = data
                data = b''
                msg_size = struct.unpack(">L", packed_msg_size)[0]
                data += sc.recv(msg_size)
                while len(data) < msg_size:
                    # esto permite obtener el la info faltante por si no se recibio el dato completo
                    data += sc.recv(1)

                frame = pickle.loads(data)
                frame = cv2.imdecode(frame,cv2.IMREAD_COLOR)


                if self.args.verbose:
                    print("[RECEP] Se recibio imagen %d" %i)

                self.cola.put(frame)
                if self.args.time:
                    end = time.time()
                    print("[RECEP] Tiempo: ", end - start)

                sc.close()
                if (i == 100): i = 0

        s.close()


class Stit(threading.Thread):
    def __init__(self, cola, colaProce, args):
        threading.Thread.__init__(self)
        self.cola = cola
        self.colaProce = colaProce
        self.args = args

    def run(self):
        i = 0

        while True:
            if self.args.time:
                print("[STIT] Tomando tiempo")
#                start = time.time()


            imagenes = []
            if self.args.verbose:
                print("[STIT] Estoy en Stit")
            stitcher = cv.createStitcher(try_use_gpu=False)

            imagenes.append(self.cola.get())
            imagenes.append(self.cola.get())
            imagenes.append(self.cola.get())
            imagenes.append(self.cola.get())

            start = time.time()
            if imagenes is None:
                print("[STIT] No se pudo leer imagen ")
            #if len(imagenes) > 4:
            #    imagenes = imagenes[0:3]
            status, pano = stitcher.stitch(imagenes)

            if status == 1:
                print("[STIT] No se unieron, se necesitan mas imagenes")
            elif status == 3:
                print("[STIT] ERR_CAMERA_PARAMS_ADJUST_FAIL")
            else:
                tiempo = time.time()
                st = datetime.datetime.fromtimestamp(tiempo).strftime('%d-%m-%YY-%H:%M:%S')
                nombre_archivo = path_capturas + "stit" + st + ".jpg"
                cv.imwrite(nombre_archivo, pano);
                if self.args.verbose:
                    print("[STIT] stitching correcto: " + nombre_archivo)
                self.colaProce.put(nombre_archivo)
                if self.args.time:
                    end = time.time()
                    print("[STIT] Tiempo: ", end - start)

                i += 1


class Proce(threading.Thread):

    def __init__(self, colaProce, args):
        threading.Thread.__init__(self)
        self.colaProce = colaProce
        self.args = args

    def run(self):
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
        while True:
            if self.args.time:
                print("[PROCE] Tomando tiempo")
#               start = time.time()
            img = self.colaProce.get()
            start = time.time()
            r = dn.detect(filtro, i, self.args.show, net, meta, img)
            print("[PROCE] ", i, " ", r)
            if self.args.time:
                end = time.time()
                print("[PROCE] Tiempo: ", end - start)
            i += 1


def drg():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Mostrar información de depuración", action="store_true")
    parser.add_argument("-s", "--show", help="Mostrar imagen final", action="store_true")
    parser.add_argument("-p", "--port", type=int, help="Puerto a recibir")
    parser.add_argument("-t", "--time", action="store_true", help="Tomar tiempos")
    parser.add_argument("-f", "--filtro", action="store_true", help="Filtrar detecciones +%80")
    args = parser.parse_args()

    if args.verbose:
        print("Depuración activada!!!")
    if args.show:
        print("Show flag!!!")
    if args.time:
        print("Tomando tiempos!!")
    if args.filtro:
        print("Filtrando detecciones!!")

    cola = Queue.Queue()
    colaProce = Queue.Queue()

    recep = Recep(cola, args)
    stit = Stit(cola, colaProce, args)
    proce = Proce(colaProce, args)

    recep.start()
    stit.start()
    proce.start()


if __name__ == '__main__':
    drg()
