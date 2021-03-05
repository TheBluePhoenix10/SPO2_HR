
# USB camera display using PyQt and OpenCV, from iosoft.blog
# Copyright (c) Jeremy P Bentham 2019
# Please credit iosoft.blog if you use the information or software in it

VERSION = "Cam_display v0.10"

import sys, time, threading, cv2
import numpy as np
from flirpy.camera.lepton import Lepton
from tifffile import imsave
import helperFunctions.skin_detector

import time
import h5py


from helperFunctions.spo2Functions import face_detect_and_thresh,spartialAverage,MeanRGB,SPooEsitmate,preprocess
from helperFunctions.leptonFunctions import grabTempValue,rawFrame,generate_colour_map,raw_to_8bit,ktof,ktoc,getFrame
from helperFunctions.csvSaver import saveCSVFromFrame
try:
    from PyQt5.QtCore import Qt
    pyqt5 = True
except:
    pyqt5 = False
if pyqt5:
    from PyQt5.QtCore import QTimer, QPoint, pyqtSignal
    from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLabel,QPushButton
    from PyQt5.QtWidgets import QWidget, QAction, QVBoxLayout, QHBoxLayout
    from PyQt5.QtGui import QFont, QPainter, QImage, QTextCursor
else:
    from PyQt4.QtCore import Qt, pyqtSignal, QTimer, QPoint
    from PyQt4.QtGui import QApplication, QMainWindow, QTextEdit, QLabel
    from PyQt4.QtGui import QWidget, QAction, QVBoxLayout, QHBoxLayout
    from PyQt4.QtGui import QFont, QPainter, QImage, QTextCursor
try:
    import Queue as Queue
except:
    import queue as Queue

IMG_SIZE    = 1280,720          # 640,480 or 1280,720 or 1920,1080
IMG_FORMAT  = QImage.Format_RGB888
DISP_SCALE  = 2                # Scaling factor for display image
DISP_MSEC   = 50                # Delay between display cycles
CAP_API     = cv2.CAP_ANY       # API: CAP_ANY or CAP_DSHOW etc...
EXPOSURE    = 0                 # Zero for automatic exposure
TEXT_FONT   = QFont("Courier", 10)

camera_num  = 1                 # Default camera (first in list)
image_queue = Queue.Queue()     # Queue to hold images
capturing   = True              # Flag to indicate capturing

colorMapType = 1

frameCount=0

globalCount=0

duration=10

totalFrame = 250

# se;f.spo2Flag=0

final_sig=[]

spo2_set=[]


vid= Lepton()





# Grab images from the camera (separate thread)

camState = 'not_recording'
tiff_frame = 1
maxVal = 0
minVal = 0




def grab_images(cam_num, queue,self):
    # global se;f.self.spo2Flagag
    global frameCount
    global globalCount
    global final_sig
    global totalFrame
    
    cap = cv2.VideoCapture(cam_num-1 + CAP_API)
    print(cam_num-1 + CAP_API)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMG_SIZE[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMG_SIZE[1])
    if EXPOSURE:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        cap.set(cv2.CAP_PROP_EXPOSURE, EXPOSURE)
    else:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    while capturing:
        if cap.grab():

            if(self.frameDifferenceFlag):
                frame = np.subtract(getFrame(),self.firstFrame)
            
            else:
                frame = getFrame()

            
                    # dataArray2d = data[40:120,25:60]
            cv2.rectangle(frame,(60,40),(100,80),(0,0,255),3)        
            frame = cv2.resize(frame,(640,480))
            print(frame.shape)
            
            retval, image = cap.retrieve(0)
            
            print(image.shape)
            

            image = cv2.resize(image,(640,480))

            

            displayImage = image.copy()
            cv2.rectangle(displayImage,(240,160),(400,320),(0,0,255),3)

            
            faceFrame = image[int(100*0.9):int(200*1.1),int(150*0.9):int(250*1.1)]

            

            finalFrame = cv2.hconcat([frame,displayImage])
            image = finalFrame
            if image is not None and queue.qsize() < 2 or (self.spo2Flag):

                if frameCount ==0 and self.spo2Flag==1:
                    
                    print("working")
                    print(final_sig)
                    thresh,mask=face_detect_and_thresh(faceFrame)
                    temp,min_value,max_value=spartialAverage(mask,faceFrame)

                    if(type(temp)==type(2)):
                        print("failed estimation, try again")
                        frameCount=totalFrame
                        # break
                        self.spo2Flag=2
                    final_sig.append(temp)
                elif (self.spo2Flag==1) and frameCount<totalFrame and frameCount>1:
                    # print("working")
                    # print(final_sig)

                    thresh,mask=face_detect_and_thresh(faceFrame)
                    final_sig.append(MeanRGB(thresh,faceFrame,final_sig[-1],min_value,max_value))

                if frameCount==totalFrame:

                    if self.spo2Flag==1:
                        result=SPooEsitmate(final_sig,totalFrame,totalFrame,duration) # the final signal list is sent to SPooEsitmate function with length of the video
                        try:
                            self.label_2.setText("Temp:"+str(grabTempValue()[0]))
                            self.label_3.setText("Min-Temp:"+str(grabTempValue()[1]))
                            self.label_4.setText("Max-Temp:"+str(grabTempValue()[2]))
                            self.label_1.setText("SPO2 Level:"+str(int(np.ceil(result))))
                        except:
                            self.label_2.setText("Temp:"+"NA")
                            self.label_3.setText("Min-Temp:"+"NA")
                            self.label_4.setText("Max-Temp:"+"NA")
                            self.label_1.setText("SPO2 Level:"+"NA")
                        
                        self.spo2Flag=0

                    elif self.spo2Flag==2:
                        self.spo2Flag=0

                        
                if self.spo2Flag!=2:
                    queue.put(image)

                frameCount=frameCount+1
                globalCount=globalCount +1
            else:
                time.sleep(DISP_MSEC / 1000.0)
        else:
            print("Error: can't grab camera image")
            break
    cap.release()

# Image widget
class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        self.setMinimumSize(image.size())
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QPoint(0, 0), self.image)
        qp.end()

# Main window
class MyWindow(QMainWindow):
    text_update = pyqtSignal(str)

    # Create main window
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        self.central = QWidget(self)
        self.textbox = QTextEdit(self.central)
        self.textbox.setFont(TEXT_FONT)
        self.textbox.setMinimumSize(300, 100)
        self.text_update.connect(self.append_text)
        self.label_1 = QLabel('SPO2 Level:',self)
        self.label_1.setStyleSheet("background-color: white; border: 1px solid black;")

        self.label_2 = QLabel('Temperature:',self)
        self.label_2.setStyleSheet("background-color: white; border: 1px solid black;")

        self.label_3 = QLabel('Min-Temp:',self)
        self.label_3.setStyleSheet("background-color: white; border: 1px solid black;")


        self.label_4 = QLabel('Max-Temp:',self)
        self.label_4.setStyleSheet("background-color: white; border: 1px solid black;")

        self.button_1= QPushButton("Start",self)
        self.button_1.clicked.connect(self.getValues)
        
        self.button_2= QPushButton("Temperature",self)
        self.button_2.clicked.connect(self.temperatureUpdate)

        self.button_3= QPushButton("Frame Difference",self)
        self.button_3.clicked.connect(self.frameDifference)
        

        self.spo2Flag=False
        self.frameDifferenceFlag = False

        self.firstFrame=[]

        sys.stdout = self
        print("Camera number %u" % camera_num)
        print("Image size %u x %u" % IMG_SIZE)
        if DISP_SCALE > 1:
            print("Display scale %u:1" % DISP_SCALE)

        self.vlayout = QVBoxLayout()        # Window layout
        self.displays = QHBoxLayout()
        self.displaysLabel = QHBoxLayout()
        self.displaysSecond = QHBoxLayout()
        self.disp = ImageWidget(self)
        self.displays.addWidget(self.disp)
        self.displaysLabel.addWidget(self.label_1)
        self.displaysLabel.addWidget(self.label_2)
        self.displaysSecond.addWidget(self.label_3)
        self.displaysSecond.addWidget(self.label_4)
        self.vlayout.addLayout(self.displays)
        self.vlayout.addLayout(self.displaysLabel)
        self.vlayout.addWidget(self.button_1)
        self.vlayout.addWidget(self.button_2)
        self.vlayout.addWidget(self.button_3)
        self.vlayout.addLayout(self.displaysSecond)

        # self.vlayout.addLayout(self.displays)
        self.label = QLabel(self)
        self.vlayout.addWidget(self.label)
        self.vlayout.addWidget(self.textbox)
        self.central.setLayout(self.vlayout)
        self.setCentralWidget(self.central)

        self.mainMenu = self.menuBar()      # Menu bar
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        self.fileMenu = self.mainMenu.addMenu('&File')
        self.fileMenu.addAction(exitAction)


    def frameDifference(self):
        self.frameDifferenceFlag = not self.frameDifferenceFlag
        self.firstFrame = getFrame()

    def temperatureUpdate(self):
        # self.label_2.setText("Temp:"+str(grabTempValue()))
        self.label_2.setText("Temp:"+str(grabTempValue()[0]))
        self.label_3.setText("Min-Temp:"+str(grabTempValue()[1]))
        self.label_4.setText("Max-Temp:"+str(grabTempValue()[2]))

    def getValues(self):
        global frameCount,final_sig
        final_sig=[]

        frameCount = 0
        self.spo2Flag=True
        self.label_1.setText("SPO2:" +" ")
        # self.label_2.setText("Temp:"+str(grabTempValue()))
        self.label_2.setText("Temp:"+str(grabTempValue()[0]))
        self.label_3.setText("Min-Temp:"+str(grabTempValue()[1]))
        self.label_4.setText("Max-Temp:"+str(grabTempValue()[2]))

        # self.label_2.setText("Temperature:" +" ")
    # Start image capture & display
    def start(self):
        self.timer = QTimer(self)           # Timer to trigger display
        self.timer.timeout.connect(lambda:
                    self.show_image(image_queue, self.disp, DISP_SCALE))
        self.timer.start(DISP_MSEC)
        self.capture_thread = threading.Thread(target=grab_images,
                    args=(camera_num, image_queue,self))
        self.capture_thread.start()         # Thread to grab images

    # Fetch camera image from queue, and display it
    def show_image(self, imageq, display, scale):
        if not imageq.empty():
            image = imageq.get()
            if image is not None and len(image) > 0:
                img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.display_image(img, display, scale)

    # Display an image, reduce size if required
    def display_image(self, img, display, scale=1):
        disp_size = img.shape[1]//scale, img.shape[0]//scale
        disp_bpl = disp_size[0] * 3
        if scale > 1:
            img = cv2.resize(img, disp_size,
                             interpolation=cv2.INTER_CUBIC)
        qimg = QImage(img.data, disp_size[0], disp_size[1],
                      disp_bpl, IMG_FORMAT)
        display.setImage(qimg)

    # Handle sys.stdout.write: update text display
    def write(self, text):
        self.text_update.emit(str(text))
    def flush(self):
        pass

    # Append to text display
    def append_text(self, text):
        cur = self.textbox.textCursor()     # Move cursor to end of text
        cur.movePosition(QTextCursor.End)
        s = str(text)
        while s:
            head,sep,s = s.partition("\n")  # Split line at LF
            cur.insertText(head)            # Insert text at cursor
            if sep:                         # New line if LF
                cur.insertBlock()
        self.textbox.setTextCursor(cur)     # Update visible cursor

    # Window is closing: stop video capture
    def closeEvent(self, event):
        global capturing
        capturing = False
        self.capture_thread.join()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            camera_num = int(sys.argv[1])
        except:
            camera_num = 0
    if camera_num < 1:
        print("Invalid camera number '%s'" % sys.argv[1])
    else:
        app = QApplication(sys.argv)
        win = MyWindow()
        win.showMaximized()
        win.setWindowTitle(VERSION)
        win.start()
        sys.exit(app.exec_())
