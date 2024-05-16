# Importing necessary libraries
import cv2 as cv
import time
import os
from twilio.rest import Client
import csv

# Twilio credentials
account_sid = 'your acc_sid'
auth_token = 'your authtoken'
twilio_phone_number = '+your tpn'
destination_phone_number = '+your dpn'

class_name = []
with open(os.path.join("project_files",'obj.names'), 'r') as f:
    class_name = [cname.strip() for cname in f.readlines()]

net1 = cv.dnn.readNet('project_files/yolov4_tiny.weights', 'project_files/yolov4_tiny.cfg')
net1.setPreferableBackend(cv.dnn.DNN_BACKEND_CUDA)
net1.setPreferableTarget(cv.dnn.DNN_TARGET_CUDA_FP16)
model1 = cv.dnn_DetectionModel(net1)
model1.setInputParams(size=(640, 480), scale=1/255, swapRB=True)

# Change to the path of your input video file
cap = cv.VideoCapture('camera1_road_view.mp4')
width  = int(cap.get(3))
height = int(cap.get(4))
result = cv.VideoWriter('result.avi', 
                         cv.VideoWriter_fourcc(*'MJPG'),
                         10,(width, height))

# Defining parameters for result saving and get coordinates
result_path = "pothole_coordinates"
starting_time = time.time()
Conf_threshold = 0.5
NMS_threshold = 0.4
frame_counter = 0
i = 0
b = 0
coordinates = []

def get_severity(box_width, frame_width):
    box_ratio = (box_width / frame_width) * 100
    if box_ratio > 15:
        return "High", box_ratio
    elif 10 <= box_ratio <= 15:
        return "Medium", box_ratio
    else:
        return "Low", box_ratio





while True:
    ret, frame = cap.read()
    frame_counter += 1
    if ret == False:
        break
    classes, scores, boxes = model1.detect(frame, Conf_threshold, NMS_threshold)
    for (classid, score, box) in zip(classes, scores, boxes):
        label = "pothole"
        x, y, w, h = box
        severity, box_ratio = get_severity(w, width)
        if len(scores) != 0 and scores[0] >= 0.7:
            if box_ratio > 0.1 and box[1] < 600:
                cv.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 1)
                cv.putText(frame, f"{severity} Severity ({box_ratio:.2f}%)", (box[0], box[1]-10), cv.FONT_HERSHEY_COMPLEX, 0.5, (255,0,0), 1)
                center_x = x + w // 2
                center_y = y + h // 2
                coordinates.append((center_x, center_y))
                if i == 0:
                    cv.imwrite(os.path.join(result_path, 'pothole' + str(i) + '.jpg'), frame)
                    with open(os.path.join(result_path, 'pothole' + str(i) + '.txt'), 'w') as f:
                        f.write(f"{center_x}, {center_y}")
                        i += 1
                        # Send message for the first pothole
                        client = Client(account_sid, auth_token)
                        message = client.messages.create(
                            body=f"Pothole detected at the following coordinates: {str((center_x, center_y))}",
                            from_=twilio_phone_number,
                            to=destination_phone_number
                        )
                    name="pothole"+str(i)
                    percentage=box_ratio
                    maxPercentage=0
                    if(maxPercentage<percentage):
                        maxPercentage=percentage
                    coord=str((center_x, center_y))
                    severity=get_severity(w,width)
                    record=[]
                    record.append(name)
                    record.append(percentage)
                    record.append(maxPercentage)
                    record.append(severity)
                    record.append(coord)
                    records=[]
                    records.append(record)
                if i != 0:
                    if (time.time() - b) >= 2:
                        cv.imwrite(os.path.join(result_path, 'pothole' + str(i) + '.jpg'), frame)
                        with open(os.path.join(result_path, 'pothole' + str(i) + '.txt'), 'w') as f:
                            f.write(f"{center_x}, {center_y}")
                            b = time.time()
                            i += 1
                    name="pothole"+str(i)
                    percentage=box_ratio
                    coord=str((center_x, center_y))
                    severity=get_severity(w,width)
                    record=[]
                    record.append(name)
                    record.append(percentage)
                    record.append(maxPercentage)
                    record.append(severity)
                    record.append(coord)
                    records.append(record)
    
                    
    endingTime = time.time() - starting_time
    fps = frame_counter / endingTime
    cv.putText(frame, f'FPS: {fps}', (20, 50), cv.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 0), 2)
    cv.imshow('frame', frame)
    result.write(frame)
    key = cv.waitKey(1)
    if key == ord('q'):
        break

print("Message sent to your authorized mobile")
unique_records = {}

    # Process the data and keep only the latest record for each pothole
for record in records:
    pothole_name = record[0]
    if pothole_name not in unique_records:
        unique_records[pothole_name] = record
        # If multiple records exist for the same pothole, keep the latest one
        # Assuming that the last record encountered is the latest one
    else:
        unique_records[pothole_name] = record
hnames=["PotholeName","Percentage","maxPercentage","Severity","Coordinates"]
# Write unique records to a CSV file
i=0
name="output"+str(i+1)+".csv"
with open(name, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(hnames)
        for record in unique_records.values():
            writer.writerow(record)


    


cap.release()
result.release()
cv.destroyAllWindows()
