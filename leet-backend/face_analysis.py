import cv2
import numpy as np
from keras.models import model_from_json
import time
from statistics import mode
import datetime
from imutils.video import FPS
import json
import face_recognition
from imutils import face_utils
import dlib
from scipy.spatial import distance as dist
import statistics

def start_exp_analysis(video_filename):


	"""
		Function to detect and classify the facial expression

		Parameters:

		video_filename (String) : Path to the videofile of lecture

		.
		.
		.
		Return:
		
		dict_count (Dictionary) : Dictionary having the face expression data of the lecture

	"""

	
	# creating object to read the video frames

	cap = cv2.VideoCapture(video_filename)

	# Get current width of frame
	width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)  # float
	
	# Get current height of frame
	height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float
	
	# fps
	fps_vid = cap.get(cv2.CAP_PROP_FPS)


	# dictionary for data to return
	dict_count = {'unhappy': 0, 'happy': 0, 'neutral': 0, 'final_score': 0}

	# list of target emotions
	face_exp = ['neutral', 'unhappy', 'happy']

	# for mode of detected candidates in all the frames
	detected = []

	## Loading trained CNN Model
	json_file = open('model210.json', 'r')
	loaded_model_json = json_file.read()
	json_file.close()
	loaded_model = model_from_json(loaded_model_json)
	# load weights into new model
	loaded_model.load_weights("model210.h5")
	print("Loaded model from disk")

	## Compiling model
	loaded_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

	# haar_cascade_face = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
	
	# for face detection object  // need to change this for better performance
	detector = face_recognition.api.dlib.get_frontal_face_detector()	

	# for frame count
	f_count = 0


	# for normalizing the image
	norm_img = np.zeros((300, 300))
	
	# for mode of the emotion detected in all frames
	emotion_all = []

	# looping till the camera object getting the value or till camera is opened
	while cap.isOpened():

		# start = time.time()
		# print(start)
		# reading video frame by frame
		ret, frame = cap.read()

		if ret == False:
			break
		#frame = cv2.resize(frame, (300, 300))
		# normalize the image
		frame = cv2.normalize(frame, norm_img, 0, 255, cv2.NORM_MINMAX)

		# image convertion to gray scale
		image_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		emot_for_set = {'unhappy': 0, 'happy': 0, 'neutral': 0}

		detection_temp = 0

		# extracting face's rectangle dimension out of the image
		# faces_rects = haar_cascade_face.detectMultiScale(image_gray, scaleFactor = 1.2, minNeighbors = 5)

		# detecting faces in frame
		faces_rects = detector(image_gray, 1)

		# iterating on number of faces 
		for i, rect in enumerate(faces_rects):
		    # eye_contact += 1
			(x, y, w, h) = face_utils.rect_to_bb(rect)

		    # croping face part out of image
			img = frame[y:y + h, x:x + w]

			try:

				# resizing and reshaping the image according to the model input dimension
				    
				resized = cv2.resize(img, (48, 48))
				reshaped = resized.reshape(-1, 48, 48, 3)

				# prediction
				emot = loaded_model.predict(reshaped)
					    
				#print(emot)
			    # index of the max percentage emotion out of list
				index = np.where(emot[0] == np.amax(emot[0]))[0]

			    # max percentage value emotion out of list
				emot_a = np.amax(emot[0])

				# plotting rectangle around face
				cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

				#print(face_exp[index[0]])

				# if the score is more than 70% for any emotion

				if emot_a >= 0.70:
					if face_exp[index[0]] == "happy":
						cv2.putText(frame, "happy" + " : " + str(emot_a), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
							(255, 255, 0), 2)

					elif face_exp[index[0]] == "unhappy":
						cv2.putText(frame, "unhappy" + " : " + str(emot_a), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
							(255, 255, 0), 2)

					else:
						cv2.putText(frame, "neutral" + " : " + str(emot_a), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
							(255, 255, 0), 2)

				#emot_for_set.append(face_exp[index[0]])
				else:
					cv2.putText(frame, "neutral", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 0), 2)
					#emot_for_set.append("neutral")
					face_exp[index[0]] = 'neutral'
				emot_for_set[face_exp[index[0]]] += 1

			except:
				print("Some Exception")
		    
			detection_temp += 1

			emotion_all.append(emot_for_set)

		    

		# showing frame
		cv2.imshow("Frame", frame)

		detected.append(detection_temp)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

		f_count += 1

	
	sum_all = 0
	per_dict = {}
	happy = []
	unhappy = []
	neutral = []


	# mode of detected candidate

	detect_mode = statistics.mode(detected)
	print("Total Detected : " + str(detect_mode))
	for i in emotion_all:
		happy.append(i['happy'])
		unhappy.append(i['unhappy'])
		neutral.append(i['neutral'])
	dict_count['happy'] = (statistics.mode(happy)/detect_mode)*100
	dict_count['unhappy'] = (statistics.mode(unhappy)/detect_mode)*100
	dict_count['neutral'] = (statistics.mode(neutral)/detect_mode)*100
	dict_count['final_score'] = dict_count['happy'] + dict_count['neutral']

	#print(dict_count)

	cap.release()
	cv2.destroyAllWindows()
	return dict_count


dictionary_get = start_exp_analysis(0)
print(dictionary_get)