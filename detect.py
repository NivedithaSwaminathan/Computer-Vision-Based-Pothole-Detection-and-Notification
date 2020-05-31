PYTHON CODE FOR DETECTION, EMAIL AND LOGGING DATA INTO DATABASE

import cv2
import numpy as np
import pygame
import cv2.cv as cv
import time
import serial
import pynmea2
import smtplib
from matplotlib import pyplot as plt
import picamera
import time
import io
from picamera import PiCamera
from time import sleep
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import string
import MySQLdb


#Capturing the image

stream = io.BytesIO()

with picamera.PiCamera() as camera:
    camera.resolution = (640, 480)
    
    time.sleep(3)
    camera.capture(stream, format='jpeg')
    
buff = np.fromstring(stream.getvalue(), dtype=np.uint8)

#Creates an OpenCV image
img = cv2.imdecode(buff , 1)

##Converts from BGR to RGB
img = img[ :, :, ::-1]


im=img.copy()

#Median filtering for image enhancement
median = cv2.medianBlur(im,5)
cv2.imshow("Enhanced Image",median)

#Greyscale conversion
grey = cv2.cvtColor( median, cv2.COLOR_RGB2GRAY )
cv2.imshow("Grayscale Image",grey)


# Setup BlobDetector
params = cv2.SimpleBlobDetector_Params()

# Change thresholds

params.minThreshold = 0;
params.maxThreshold = 255;
	 

params.filterByColor = True
params.blobColor = 255


# Filter by Area.
params.filterByArea = True
params.minArea = 100
	 
# Filter by Circularity
params.filterByCircularity = True
params.minCircularity = 0.25
params.maxCircularity = 1
 
# Filter by Convexity
params.filterByConvexity = True
params.minConvexity = 0.5

# Filter by Inertia
params.filterByInertia = True
params.minInertiaRatio = 0.01
params.maxInertiaRatio = 1

params.minRepeatability = 2;

	 
# Create a detector with the parameters
detector = cv2.SimpleBlobDetector(params)

keypoints = detector.detect(median)


# Draw detected blobs as red circles.
# cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
im_with_keypoints = cv2.drawKeypoints(im, keypoints, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)


n = len(keypoints)
print ("No of potholes detected:")
print (n)
print ("Their coordinates:")
print (keypoints)

cv2.imwrite('result.jpg',im_with_keypoints)
time.sleep(5)

##Variables for MySQL
db = MySQLdb.connect(host="localhost", user = "root", passwd = "abcde", db= "mydb")
cur = db.cursor()

if n!=0:

#Sending the mail
    email_user = 'thatsmeniveditha@gmail.com'
    email_password = 'Cr00ksh@nks'
    email_send = 'thatsmeniveditha@gmail.com'

    subject = 'POTHOLE DETECTED'

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_send
    msg['Subject'] = subject
    
    #setup the serial port to which gps is connected 
    port = "/dev/ttyAMA0"
    ser = serial.Serial(port, baudrate = 9600, timeout = 0.5)
    dataout  = pynmea2.NMEAStreamReader()

    
    while True:
##        Reading values from GPS
        newdata = ser.readline()
    
        if newdata[0:6] == '$GPGGA':
            newmsg = pynmea2.parse(newdata)
            newlat = newmsg.latitude
            newlong = newmsg.longitude
            lat  = str(newlat)
            lon = str(newlong)
            content = "Pothole detected at http://maps.google.com/maps?q=" + lat + "," + lon
            Email = content
            msg.attach(MIMEText(Email, 'plain'))
            
            
            filename = 'result.jpg'
            attachment = open(filename, 'rb')

            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= "+filename)

            msg.attach(part)
            text = msg.as_string()
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_user, email_password)

            server.sendmail(email_user, email_send, text)
            server.quit()
            
            print ("Mail sent!")
            time.sleep(3)
            
            sql = ("""INSERT INTO Pothole_Location (Latitude,Longitude) VALUES (%s,%s) """,(newlat,newlong))
            
            try:
                print ("Writing to database....")
##                Execute the SQL command
                cur.execute(*sql)
##                commit your changes in the database
                db.commit()
                print ("Write complete!")
                
            except:
##                Rollback in case there is any error
                db.rollback()
                print ("Failed writing to database")
            cur.close()
            db.close()
            break
                
    # Show keypoints
##cv2.imshow("Keypoints", im_with_keypoints)
##cv2.waitKey(0)


