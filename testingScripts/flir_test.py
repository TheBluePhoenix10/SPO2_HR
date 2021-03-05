# import the opencv library 
import cv2 
from flirpy.camera.lepton import Lepton
import numpy
import sys
import pyperclip
numpy.set_printoptions(threshold=sys.maxsize)
# define a video capture object 
vid = Lepton() 

def getFrame():
    global tiff_frame
    global camState
    global maxVal
    global minVal
    data = q.get(True, 500)
    if data is None:
        print('No Data')
    if camState == 'recording':
        startRec.hdf5_file.create_dataset(('image'+str(tiff_frame)), data=data)
        tiff_frame += 1
    #Cannot you cv2.resize on raspberry pi 3b+. Not enough processing power.
    #data = cv2.resize(data[:,:], (640, 480))
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(data)
    img = cv2.LUT(raw_to_8bit(data), generate_colour_map())
    #display_temperature only works if cv2.resize is used
    #display_temperatureK(img, minVal, minLoc, (255, 0, 0)) #displays min temp at min temp location on image
    #display_temperatureK(img, maxVal, maxLoc, (0, 0, 255)) #displays max temp at max temp location on image
    #display_temperatureK(img, minVal, (10,55), (255, 0, 0)) #display in top left corner the min temp
    #display_temperatureK(img, maxVal, (10,25), (0, 0, 255)) #display in top left corner the max temp
    return img

while(True): 
      
    # Capture the video frame 
    # by frame 
    frame = vid.grab() 
#    frame=    threshold_slow(frame)
    # Display the resulting frame
    print(frame.shape) 
    cv2.imshow('frame', frame) 
    # the 'q' button is set as the 
    # quitting button you may use any 
    # desired button of your choice 
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break
  
# After the loop release the cap object 
vid.close() 
# Destroy all the windows 
cv2.destroyAllWindows() 
