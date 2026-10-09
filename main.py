import traceback

try:
    import os
    import json
    import numpy as np
    from collections import deque
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.clock import Clock
    from kivy.core.window import Window
    from plyer import accelerometer, gyroscope
    
    # Buildozer uses tflite_runtime, desktop testing uses standard tensorflow
    try:
        import tflite_runtime.interpreter as tflite
    except ImportError:
        import tensorflow.lite as tflite

    class ActivityRecognizerLayout(BoxLayout):
        def __init__(self, **kwargs):
            super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)
            self.is_detecting = False
            self.buffer = deque(maxlen=50) # Strict 1-second buffer
            self.step_counter = 0
            
            self.load_model_and_labels()
            
            self.status_label = Label(text="AI Engine Ready", size_hint=(1, 0.15))
            self.add_widget(self.status_label)
            
            self.prediction_label = Label(
                text="IDLE", 
                font_size='30sp', 
                bold=True, 
                size_hint=(1, 0.4)
            )
            self.add_widget(self.prediction_label)
            
            self.confidence_label = Label(text="Confidence: 0.00%", size_hint=(1, 0.15))
            self.add_widget(self.confidence_label)
            
            self.toggle_btn = Button(
                text="START DETECTION", 
                background_color=(0, 1, 0, 1), 
                size_hint=(1, 0.3)
            )
            self.toggle_btn.bind(on_press=self.toggle_detection)
            self.add_widget(self.toggle_btn)

        def load_model_and_labels(self):
            # Load JSON Labels
            with open('labels.json', 'r') as f:
                self.labels = json.load(f)
                
            # Load TFLite Model
            self.interpreter = tflite.Interpreter(model_path="activity_model.tflite")
            self.interpreter.allocate_tensors()
            
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()

        def toggle_detection(self, instance):
            if self.is_detecting:
                self.stop_detection()
            else:
                self.start_detection()

        def start_detection(self):
            self.is_detecting = True
            self.buffer.clear()
            self.step_counter = 0
            self.toggle_btn.text = "STOP DETECTION"
            self.toggle_btn.background_color = (1, 0, 0, 1)
            self.status_label.text = "Monitoring sensors at 50Hz..."
            
            try:
                accelerometer.enable()
                gyroscope.enable()
            except NotImplementedError:
                pass
            Clock.schedule_interval(self.log_and_predict, 1.0 / 50.0)

        def log_and_predict(self, dt):
            try:
                try:
                    accel = accelerometer.acceleration
                    if accel is None or accel == (None, None, None): accel = (0.0, 0.0, 0.0)
                except NotImplementedError:
                    accel = (0.0, 0.0, 0.0)
                    
                try:
                    gyro = gyroscope.rotation
                    if gyro is None or gyro == (None, None, None): gyro = (0.0, 0.0, 0.0)
                except NotImplementedError:
                    gyro = (0.0, 0.0, 0.0)
                    
                # Append exactly 6 features matching Colab training shape
                self.buffer.append([accel[0], accel[1], accel[2], gyro[0], gyro[1], gyro[2]])
                self.step_counter += 1
                
                # Run inference every 25 steps (0.5 second overlap) once buffer is full
                if len(self.buffer) == 50 and self.step_counter >= 25:
                    self.step_counter = 0
                    self.run_inference()
            except Exception as e:
                self.status_label.text = f"Sensor Error: {str(e)}"

        def run_inference(self):
            try:
                # Format data to shape (1, 50, 6)
                input_data = np.array(self.buffer, dtype=np.float32).reshape(1, 50, 6)
                
                # Feed data into the model
                self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
                self.interpreter.invoke()
                
                # Extract probabilities
                output_data = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                class_idx = np.argmax(output_data)
                confidence = output_data[class_idx]
                
                predicted_activity = self.labels.get(str(class_idx), "Unknown")
                self.prediction_label.text = predicted_activity
                self.confidence_label.text = f"Confidence: {confidence:.2%}"
                
                # Visual Theft Alert
                if "Theft" in predicted_activity and confidence > 0.70:
                    self.prediction_label.color = (1, 0.2, 0.2, 1) # Red Alert
                else:
                    self.prediction_label.color = (1, 1, 1, 1) # White Normal
            except Exception as e:
                self.status_label.text = f"Inference Error: {str(e)}"

        def stop_detection(self):
            self.is_detecting = False
            Clock.unschedule(self.log_and_predict)
            try:
                accelerometer.disable()
                gyroscope.disable()
            except NotImplementedError:
                pass
            self.toggle_btn.text = "START DETECTION"
            self.toggle_btn.background_color = (0, 1, 0, 1)
            self.status_label.text = "AI Engine Ready"
            self.prediction_label.text = "IDLE"
            self.prediction_label.color = (1, 1, 1, 1)
            self.confidence_label.text = "Confidence: 0.00%"

    class AIActivityApp(App):
        def build(self):
            return ActivityRecognizerLayout()

    if __name__ == '__main__':
        AIActivityApp().run()
        
except Exception:
    error_log = traceback.format_exc()
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    from kivy.core.window import Window
    
    class CrashReporterApp(App):
        def build(self):
            Window.clearcolor = (0.5, 0, 0, 1) 
            scroll = ScrollView()
            label = Label(text=error_log, font_size='12sp', text_size=(Window.width * 0.9, None), size_hint_y=None, halign='left', valign='top')
            label.bind(texture_size=label.setter('size'))
            scroll.add_widget(label)
            return scroll
            
    if __name__ == '__main__':
        CrashReporterApp().run()