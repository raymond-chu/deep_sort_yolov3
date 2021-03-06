#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import

import os
from timeit import time
import warnings
import sys
import cv2
import numpy as np
from PIL import Image
from yolo import YOLO

from deep_sort import preprocessing
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from tools import generate_detections as gdet
from deep_sort.detection import Detection as ddet
from videocaptureasync import VideoCaptureAsync
warnings.filterwarnings('ignore')


def main(yolo):

   # Definition of the parameters
    max_cosine_distance = 0.1
    nn_budget = None
    nms_max_overlap = 1.0

    # counter
    tr_occupied = []
    tr_vacant = []

   # deep_sort
    model_filename = 'model_data/mars-small128.pb'
    encoder = gdet.create_box_encoder(model_filename, batch_size=1)

    metric = nn_matching.NearestNeighborDistanceMetric(
        "cosine", max_cosine_distance, nn_budget)
    tracker = Tracker(metric)

    writeVideo_flag = True

    video_capture = cv2.VideoCapture('20200130_154806A_Trim_Trim.mp4')
    # video_capture = cv2.VideoCapture(0)
    cap = VideoCaptureAsync()
    cap.start()

    if writeVideo_flag:
        # Define the codec and create VideoWriter object
        w = int(video_capture.get(3))
        h = int(video_capture.get(4))
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter('output.avi', fourcc, 15, (w, h))
        list_file = open('detection.txt', 'w')
        frame_index = -1

    fps = 0.0
    while True:
        # ret, frame = video_capture.read()  # frame shape 640*480*3
        _, frame = cap.read()
        # if ret != True:
        # break
        t1 = time.time()

       # image = Image.fromarray(frame)
        image = Image.fromarray(frame[..., ::-1])  # bgr to rgb
        boxs, out_class, out_score = yolo.detect_image(image)
       # print("box_num",len(boxs))
        features = encoder(frame, boxs)

        # score to 1.0 here).
        detections = [Detection(bbox, 1.0, feature)
                      for bbox, feature in zip(boxs, features)]

        # Run non-maxima suppression.
        boxes = np.array([d.tlwh for d in detections])
        scores = np.array([d.confidence for d in detections])
        indices = preprocessing.non_max_suppression(
            boxes, nms_max_overlap, scores)
        detections = [detections[i] for i in indices]

        # if len(out_class) != 0:

        # Call the tracker
        tracker.predict()
        tracker.update(detections)

        for track in tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            if len(out_class) != 0:
                for object in out_class:
                    if object == 0 and track.track_id not in tr_vacant:
                        tr_vacant.append(track.track_id)
                    elif object == 1 and track.track_id not in tr_occupied:
                        tr_occupied.append(track.track_id)
            bbox = track.to_tlbr()
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (255, 255, 255), 2)
            cv2.putText(frame, str(track.track_id), (int(bbox[0]), int(bbox[1])), 0, 5e-3 * 200, (0, 255, 0), 2)

        for index, det in enumerate(detections):
            bbox = det.to_tlbr()
            if len(out_class) != 0:
                if out_class[index] == 0:
                    object_class = 'vacant'
                    box_colour = (128,0,128)
                elif out_class[index] == 1:
                    object_class = 'occupied'
                    box_colour = (0,255,0)
            if len(out_score) != 0:
                object_score = out_score[0] 
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), box_colour, 2)
            cv2.putText(frame, "    " + object_class + " " + str(int(object_score * 100)) + "%", (int(bbox[0]), int(bbox[1])), 0, 5e-3 * 200, box_colour, 2)

        cv2.putText(frame, "Occupied: " + str(len(tr_occupied)) + " Vacant: " + str(len(tr_vacant)), (10, 1000), 0, 2, (255, 255, 0), 2)

        cv2.imshow('', frame)

        if writeVideo_flag:
            # save a frame
            out.write(frame)
            frame_index = frame_index + 1
            list_file.write(str(frame_index)+' ')
            if len(boxs) != 0:
                for i in range(0, len(boxs)):
                    list_file.write(str(
                        boxs[i][0]) + ' '+str(boxs[i][1]) + ' '+str(boxs[i][2]) + ' '+str(boxs[i][3]) + ' ')
            list_file.write('\n')

        fps  = ( fps + (1./(time.time()-t1)) ) / 2
        print("fps= %f" % (fps))

        # Press Q to stop!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
        # Press R to reset counter!
        elif cv2.waitKey(33) & 0xFF == ord('r'):
            tr_vacant = []
            tr_occupied = []

    video_capture.release()
    cap.stop()
    cap.release()
    if writeVideo_flag:
        out.release()
        list_file.close()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main(YOLO())
