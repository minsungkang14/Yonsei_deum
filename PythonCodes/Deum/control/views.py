from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError, StreamingHttpResponse

from django.views.decorators import gzip
from socket import *
import numpy as np
import struct
import cv2
import time
import threading


ip = '192.168.219.118'
# ip = '127.0.0.1'
port = 8888

clientSock = socket(AF_INET, SOCK_STREAM)
print("connect start")
clientSock.connect((ip, port))
print("connect success")

def get_image():
    bin_data = clientSock.recv(1536)
    # print("len bin data", len(bin_data))
    count = int(len(bin_data) / 2)
    short_arr = struct.unpack('<' + ('h' * count), bin_data)
    np.asarray(short_arr)

    try:
        short_arr = np.reshape(short_arr, (24, 32))
        img = np.zeros((24, 32, 3), np.uint8)
        # make_hsv(short_arr, img)
        frame = absolute_HSV_Control(short_arr, img)
        return True, frame
    except:
        print("Fail")
        return False, None





class VideoCamera(object):
    def __init__(self):
        # self.video = cv2.VideoCapture(0)

        (self.grabbed, self.frame) = get_image()
        threading.Thread(target=self.update, args=()).start()

    # def __del__(self):
    #     self.video.release()

    def get_frame(self):
        image = self.frame
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def update(self):
        while True:
            (self.grabbed, self.frame) = get_image()


cam = VideoCamera()


def gen(camera):
    while True:
        frame = cam.get_frame()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')





def index(request):

    return render(request, 'control/index.html', {})



def absolute_HSV_Control (data, img):

    thickness = 2
    org = ( 2, 478 )
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 1.2

    for py in range(24):
        for px in range(32):
            value_2 = 255
            value_3 = 255
            if 3000 >= data[py][px] > 2000: #2000 = 200C  max = 300
                value_1 = 1
                value_2 = 255 - ((data[py][px] - 2000) * 254 / 1000) ## 0 = white
            elif data[py][px] > 1000 :
                value_1 =  10 - ((data[py][px] - 1000)*9 / 1000)
            elif data[py][px] > 800 :
                value_1 = 25 - ((data[py][px] - 800)*15 / 200)
            elif data[py][px] > 600 :
                value_1 = 45 - ((data[py][px] - 600)*20 / 200)
            elif data[py][px] > 400 :
                value_1 = 90 - ((data[py][px] - 400)*45 / 200)
            elif data[py][px] > 200 :
                value_1 = 135 - ((data[py][px] - 200)*45 / 200)
            elif data[py][px] > 0 :
                value_1 = 175 - ((data[py][px] )*40 / 200)
            elif data[py][px] > -100:
                value_1 = 179 - ((data[py][px] + 100 )*4 / 100)
            elif data[py][px] >= -300 :
                value_1 = 179
                value_3 = ((data[py][px] + 300) * 254 / 200) ## 0 = black


            img[py][px][0] = int(value_1)  # 0~180
            img[py][px][1] = int(value_2)
            img[py][px][2] = int(value_3)

    max_tmp = np.amax(data) / 10
    text_for_display = "max_temp: " + str(max_tmp) + "  [deum_Yonsei]"
    img = cv2.cvtColor(img, cv2.COLOR_HSV2RGB)
    img = cv2.resize(img, None, fx=20, fy=20, interpolation=cv2.INTER_CUBIC)
    cv2.putText(img, text_for_display, org, font , fontScale , (255,255,255) , thickness , cv2.LINE_AA)
    # cv2.imshow('frame', img)
    # cv2.waitKey(1)
    return img



@gzip.gzip_page
def run(request):

    try:
        return StreamingHttpResponse(gen(VideoCamera()),
                                     content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        print("getting image fail")
        pass


