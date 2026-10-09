Real-Time Android-Based Theft Anomaly Detection Using Edge AI

A data-science capstone project that investigates whether smartphone inertial-sensor sequences can distinguish simulated theft-related movements from routine human activities. The project combines Android data collection, session-aware time-series preprocessing, an LSTM classifier, TensorFlow Lite conversion, and an on-device inference prototype.


Project status: Proof of concept for academic evaluation. The reported results come from the supplied dataset and notebook. They are not a production-security benchmark and should not be interpreted as proof that theft has occurred.

Project information

•
Author: Lebogang Collin Lojane

•
Student number: 202224544

•
Institution: Sol Plaatje University

•
Department: Computer Science & Information Technology

•
Supervisor: Mrs Nthabiseng Modiba

•
Methodology: CRISP-DM adapted for smartphone time-series data and edge deployment

Problem statement

Most smartphone recovery controls are reactive: the owner must first notice that the phone is missing and then attempt to locate, lock, or erase it. This project explores an additional local signal: using the phone's accelerometer and gyroscope to recognise movement sequences that resemble simulated theft events while the event is occurring.

The system is designed as a user-mediated alert prototype. A model prediction is only an estimate and must not trigger irreversible actions automatically without confirmation.

Objectives

1.
Collect labelled accelerometer and gyroscope readings through a custom Android application.

2.
Store recordings in SQLite and export them to CSV for analysis.

3.
Prepare session-aware time-series windows for supervised learning.

4.
Compare a two-second baseline with a one-second final window configuration.

5.
Train a twelve-class LSTM activity classifier.

6.
Convert the model to TensorFlow Lite for local Android inference.

7.
Document performance, risks, limitations, and reproducibility requirements.

System overview

Plain Text


Android sensors
      |
      v
Labelled SQLite sessions
      |
      v
CSV export + validation
      |
      v
Jitter/scaling augmentation
      |
      v
Session-aware windows (50 x 6)
      |
      v
Two-layer LSTM classifier
      |
      v
TensorFlow Lite conversion
      |
      v
Android rolling-buffer inference
      |
      v
Confidence-based activity/theft alert



Dataset and final experiment

The supplied project evidence contains two main CSV files:

Dataset stage
Rows
Session identifiers
Purpose
Original sensor data
17,943
46
Primary collected observations
Augmented sensor data
53,829
138
Jittered/scaled modelling file
Final one-second windows
—
—
1,938 windows of shape (50, 6)




The final experiment used:

•
50 samples per window

•
25-sample step size

•
Six input features: accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z

•
12 activity classes

•
1,550 training windows and 388 test/validation windows using the recorded 80/20 split

•
Observed median sampling rate of approximately 41.4 Hz; the collection loop was configured for 50 Hz

Activity labels

The class mapping is stored in labels.json:

•
Abnormal_Fall

•
Normal_Jumping

•
Normal_Running

•
Normal_Sitting

•
Normal_Stairs_Down

•
Normal_Stairs_Up

•
Normal_Standing

•
Normal_Walking

•
Theft_Bag_Grab

•
Theft_Hand_Snatch

•
Theft_Pocket_Snatch

•
Theft_Running_Away

Model architecture

The final classifier is a compact stacked Long Short-Term Memory network:

Layer
Configuration
Input
(50, 6) time-series sequence
LSTM 1
64 units, returns sequences
Dropout
0.5
LSTM 2
32 units
Dropout
0.5
Dense
32 units, ReLU activation
Output
12 units, Softmax activation
Optimiser
Adam
Loss
Categorical cross-entropy
Training
40 epochs
Trainable parameters
32,044




Results

The recorded notebook run reported:

•
Final validation/test accuracy: 88.40%

•
Final validation/test loss: 0.3474

•
Training accuracy shown in the report: 85.23%

•
Two-second baseline accuracy: 72.32%

•
Final one-second window accuracy: 88.40%

The result is promising for a controlled proof of concept. However, accuracy alone is insufficient for a security application. Future evaluations should report theft-class recall, routine false-positive rate, macro F1, calibration, session-level holdout performance, and testing on genuinely unseen users and devices.

Repository contents

File
Purpose
Capstone_Project_(SPU).ipynb
Main modelling notebook, experiments, metrics, and figures
main_data_collection.py
Kivy Android data-collection application using SQLite
main.py
Kivy Android inference application using the TensorFlow Lite model
augment_data.py
Data augmentation script for jittered and scaled sensor readings
sensor_data.csv
Original collected sensor observations
sensor_data_augmented.csv
Augmented modelling dataset
activity_model.tflite
Converted TensorFlow Lite model
labels.json
Integer-to-activity label mapping
buildozer.spec
Buildozer Android packaging configuration
myapp-0.1-arm64-v8a_armeabi-v7a-debug.apk
Supplied debug APK artifact
README.md
Project documentation




Requirements

Python modelling environment

The notebook expects a Python environment with common data-science and TensorFlow packages. A typical environment includes:

Bash


python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy pandas matplotlib seaborn scikit-learn tensorflow jupyter



If the notebook specifies different versions, use those versions for exact reproduction. The notebook is the authoritative record of the executed experiment.

Android application environment

The Android prototype is based on Kivy, Plyer, NumPy, and TensorFlow Lite Runtime. The supplied buildozer.spec lists the following application requirements:

Plain Text


python3,kivy,plyer,numpy,tflite-runtime,charset-normalizer==3.3.2



Buildozer and the Android SDK/NDK are required for rebuilding the APK. Android builds are platform-dependent and may require additional configuration on Linux.

Running the notebook

From the repository root:

Bash


source .venv/bin/activate
jupyter notebook Capstone_Project_\(SPU\).ipynb



Run the notebook cells in order. Confirm that the expected input files are in the same directory as the notebook:

•
sensor_data.csv

•
sensor_data_augmented.csv

•
labels.json

The notebook contains the baseline window experiment, final one-second-window experiment, training output, evaluation output, confusion matrices, and TensorFlow Lite conversion.

Augmenting the dataset

The augmentation script creates a modelling file from the original sensor data. Review the script before running it if the output file already exists.

Bash


python augment_data.py



The augmentation process must be treated carefully in evaluation. Augmented copies derived from the same original recording should not be allowed to leak across training and test partitions in a production-quality validation design.

Android application

Data collection app

main_data_collection.py:

•
Lets the collector select an activity label.

•
Records accelerometer and gyroscope values.

•
Uses a session identifier for each recording.

•
Stores data in SQLite.

•
Exports collected rows to sensor_data.csv.

Inference app

main.py:

•
Loads activity_model.tflite and labels.json.

•
Maintains a rolling buffer of 50 sensor frames.

•
Produces a prediction every 25 new frames after the buffer is full.

•
Displays the predicted activity and confidence.

•
Shows a visual theft alert when a theft-labelled class exceeds the configured confidence threshold of 0.70.

Building the APK

With Buildozer installed and configured:

Bash


buildozer android debug



The generated APK is normally placed in the bin/ directory. The repository includes a supplied debug APK for reference, but APK files should be independently verified before installation or distribution.

Reproducibility checklist

Before claiming that the experiment has been reproduced, record:

•
Python version

•
TensorFlow/Keras version

•
NumPy, pandas, scikit-learn, and matplotlib versions

•
Android device model and Android version

•
Sensor sampling behaviour and missing-value handling

•
Random seeds and train/test split procedure

•
Whether augmentation occurred before or after partitioning

•
Exact notebook cell order and execution date

•
Model file checksum

•
Evaluation metrics beyond accuracy

Risks and limitations

•
The data were collected in a controlled project setting rather than a large real-world theft dataset.

•
The activity classes include simulated theft movements; they do not represent verified theft incidents.

•
Limited participant, device, orientation, and environmental diversity may reduce generalisation.

•
The observed sampling rate differs from the configured target rate.

•
Augmentation can create leakage if related copies cross the train/test boundary.

•
Battery use, inference latency, thermal behaviour, and long-term background operation were not formally benchmarked in the supplied evidence.

•
A false positive could create stress or unnecessary intervention.

•
A false negative could create a misleading sense of security.

•
The model should not automatically wipe, lock, contact authorities, or make other irreversible decisions.

Responsible-use recommendation

Use the classifier as one signal in a graduated response:

1.
Detect a high-confidence pattern.

2.
Give the user an audible/visual alert.

3.
Provide a short cancellation or confirmation window.

4.
Escalate only after additional evidence or user confirmation.

5.
Log the event in a privacy-preserving way.

Do not use this prototype for surveillance, law-enforcement decisions, or automated accusations.

References

•
Anguita, D., Ghio, A., Oneto, L., Parra, X., & Reyes-Ortiz, J. L. (2013). A public domain dataset for human activity recognition using smartphones. ESANN.

•
Chapman, P., Clinton, J., Kerber, R., Khabaza, T., Reinartz, T., Shearer, C., & Wirth, R. (2000). CRISP-DM 1.0: Step-by-step data mining guide.

•
Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. Neural Computation, 9(8), 1735–1780.

•
Mekruksavanich, S., & Jitpattanakul, A. (2021). LSTM networks using smartphone sensor data for human activity recognition. Sensors.

•
Schröer, C., Kruse, F., & Gómez, J. M. (2021). A systematic literature review on applying CRISP-DM process model. Procedia Computer Science.

•
Google. (2026). LiteRT: High-performance on-device machine learning.

•
TensorFlow Developers. (2023). Working with RNNs.

Full references and the extended academic discussion are provided in the capstone report.

Academic note

This repository supports the Sol Plaatje University capstone project presentation and report. It is intended for academic review, reproducibility discussion, and further experimentation. The repository should be updated with the real GitHub URL.




