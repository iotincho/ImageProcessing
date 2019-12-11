#!/usr/bin/env python
# -*- coding: utf-8 -*-
import Queue
import threading
import socket
import ivport
import time
import sys
import argparse
import signal
import pickle
import struct
import cv2

path_capturas = "/home/pi/ImageProcessing/multiplexV2/CapturasFast/"

class Envio(threading.Thread):
  def __init__(self, cola, args):
     threading.Thread.__init__(self)
     self.cola = cola
     self.args = args
     self.shutdown_flag = threading.Event()

  def run(self):

    host = "localhost"
    port = 9996
    if self.args.port:
        port = self.args.port
    if self.args.ip:
        host = str(self.args.ip)
    while not self.shutdown_flag.is_set():
        if self.args.time:
             print("[ENVIO] Tomando tiempo")
             start = time.time()
        s = socket.socket()

        photo = self.cola.get()
        try:
            s.connect((host, port))
            if self.args.verbose:
                print "[ENVIO] Se establecio conexion con: ",host,port
        except socket.error, exc:
            print "[ENVIO] No se pudo conectar con Tegra : %s" % exc


        s.send('IMAGE')
        data = pickle.dumps(photo, 0)
        size = len(data)
        try:
            s.sendall(struct.pack(">L", size) + data)
        except socket.error, exc:
            print "[ENVIO] No se pudo enviar : %s" % exc
            s.close()
            break


        if self.args.verbose:
            print "[ENVIO] Se envio archivo: "
        if self.args.time:
            end = time.time()
            print("[ENVIO] Tiempo: ",end - start)

class Captura(threading.Thread):
   def __init__(self, cola, args):
       threading.Thread.__init__(self)
       self.cola = cola
       self.args = args
       self.shutdown_flag = threading.Event()
       self._encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

   def run(self):
       iv = ivport.IVPort(ivport.TYPE_QUAD2, iv_jumper='A')
       iv.camera_open(camera_v2=True, resolution=(1024,768))
       i=0
       while not self.shutdown_flag.is_set():
           if self.args.time:
                print "[CAPTURA] Tomando tiempo"
                start = time.time()

           iv.camera_change(1)
           photo = iv.get_photo(use_video_port=False)
           photo = cv2.imencode('.jpg', photo, self._encode_params)
           if self.args.verbose:
               print '[Captura] Captura1!\n'
           self.cola.put(photo)

           iv.camera_change(2)
           photo = iv.get_photo(use_video_port=False)
           photo = cv2.imencode('.jpg', photo, self._encode_params)
           if self.args.verbose:
               print '[Captura] Captura2!\n'
           self.cola.put(photo)

           iv.camera_change(3)
           photo = iv.get_photo(use_video_port=False)
           photo = cv2.imencode('.jpg', photo, self._encode_params)
           if self.args.verbose:
               print '[Captura] Captura3!\n'
           self.cola.put(photo)

           iv.camera_change(4)
           photo = iv.get_photo(use_video_port=False)
           photo = cv2.imencode('.jpg', photo, self._encode_params)
           if self.args.verbose:
               print '[Captura] Captura4!\n'
           self.cola.put(photo)
           i += 1
           if self.args.time:
                    end = time.time()
                    print "[CAPTURA] Tiempo: ",end - start

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

    try:

        cola =  Queue.Queue()
        envio = Envio(cola, args)
        captura = Captura(cola, args)
        envio.start()
        captura.start()

        while True:
            time.sleep(0.5)

    except ServiceExit:

        envio.shutdown_flag.set()
        captura.shutdown_flag.set()
        # Wait for the threads to close...
        envio.join()
        envio.join()
if __name__ == '__main__':
   main()
