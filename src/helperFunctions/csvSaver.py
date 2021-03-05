import csv
import datetime

def saveCSVFromFrame(frame):
    space=[['-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-']]
    date = datetime.datetime.now()
    with open("data/"+x,"a") as my_csv:
        my_csvWriter = my_csv.writer(my_csv,delimiter=",")
        my_csvWriter.writerows(frame)
        my_csvWriter.writerows(space)

