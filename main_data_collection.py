import traceback

try:
    import sqlite3
    import time
    import uuid
    import os
    import csv
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.spinner import Spinner
    from kivy.uix.label import Label
    from kivy.clock import Clock
    from kivy.core.window import Window
    from plyer import accelerometer, gyroscope
    from kivy.utils import platform

    class DataCollectorLayout(BoxLayout):
        def __init__(self, **kwargs):
            super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)
            self.is_recording = False
            self.session_id = None
            self.remaining_time = 0
            self.data_buffer = [] 
            self.db_path = os.path.join(App.get_running_app().user_data_dir, 'sensor_data.db')
            self.init_sqlite_db()
            
            self.activity_durations = {
                'Normal_Walking': 20, 'Normal_Running': 20, 'Normal_Sitting': 10,
                'Normal_Standing': 10, 'Normal_Jumping': 10, 'Normal_Stairs_Up': 20,
                'Normal_Stairs_Down': 20, 'Theft_Pocket_Snatch': 5, 'Theft_Hand_Snatch': 5,
                'Theft_Bag_Grab': 5, 'Theft_Running_Away': 10, 'Abnormal_Fall': 5
            }
            
            self.status_label = Label(text="Status: Ready (SQLite Active)", size_hint=(1, 0.15))
            self.add_widget(self.status_label)
            
            self.label_spinner = Spinner(text='Select Activity', values=tuple(self.activity_durations.keys()), size_hint=(1, 0.15))
            self.add_widget(self.label_spinner)
            
            self.record_btn = Button(text="START RECORDING", background_color=(0, 1, 0, 1), size_hint=(1, 0.25))
            self.record_btn.bind(on_press=self.handle_record_button)
            self.add_widget(self.record_btn)
            
            self.data_readout = Label(text="X: 0.00 | Y: 0.00 | Z: 0.00", size_hint=(1, 0.15))
            self.add_widget(self.data_readout)

            self.export_btn = Button(text="EXPORT DB TO CSV", background_color=(0, 0.5, 1, 1), size_hint=(1, 0.2))
            self.export_btn.bind(on_press=self.export_to_csv)
            self.add_widget(self.export_btn)

            self.records_count_label = Label(text="Total Saved Sessions: 0", size_hint=(1, 0.1))
            self.add_widget(self.records_count_label)
            self.update_session_count()

        def init_sqlite_db(self):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS sensor_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, timestamp REAL, activity_label TEXT, device_orientation TEXT, accel_x REAL, accel_y REAL, accel_z REAL, gyro_x REAL, gyro_y REAL, gyro_z REAL)''')
            conn.commit()
            conn.close()

        def update_session_count(self):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(DISTINCT session_id) FROM sensor_logs")
                count = cursor.fetchone()[0]
                conn.close()
                self.records_count_label.text = f"Total Saved Sessions: {count}"
            except Exception:
                pass

        def handle_record_button(self, instance):
            if self.label_spinner.text == 'Select Activity':
                self.status_label.text = "Error: Select an activity first!"
                return
            if self.is_recording:
                self.stop_recording(aborted=True)
            else:
                self.start_recording()

        def start_recording(self):
            self.is_recording = True
            self.session_id = str(uuid.uuid4())
            self.data_buffer = [] 
            self.export_btn.disabled = True 
            self.remaining_time = self.activity_durations[self.label_spinner.text]
            self.record_btn.background_color = (1, 0, 0, 1)
            self.update_ui_timer() 
            self.status_label.text = f"Recording: {self.label_spinner.text}"
            try:
                accelerometer.enable()
                gyroscope.enable()
            except NotImplementedError:
                pass
            Clock.schedule_interval(self.log_sensor_data, 1.0 / 50.0) 
            Clock.schedule_interval(self.countdown_tick, 1.0)

        def countdown_tick(self, dt):
            self.remaining_time -= 1
            if self.remaining_time <= 0:
                self.stop_recording(aborted=False)
            else:
                self.update_ui_timer()

        def update_ui_timer(self):
            self.record_btn.text = f"STOP RECORDING ({self.remaining_time}s)"

        def log_sensor_data(self, dt):
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
                current_orientation = 'Landscape' if Window.width > Window.height else 'Portrait'
                self.data_readout.text = f"Acc X: {accel[0]:.2f} | Y: {accel[1]:.2f} | Z: {accel[2]:.2f}"
                self.data_buffer.append((self.session_id, time.time(), self.label_spinner.text, current_orientation, accel[0], accel[1], accel[2], gyro[0], gyro[1], gyro[2]))
            except Exception as e:
                print(f"Logging error: {e}")

        def stop_recording(self, aborted=False):
            self.is_recording = False
            Clock.unschedule(self.log_sensor_data)
            Clock.unschedule(self.countdown_tick)
            try:
                accelerometer.disable()
                gyroscope.disable()
            except NotImplementedError:
                pass
            self.record_btn.text = "START RECORDING"
            self.record_btn.background_color = (0, 1, 0, 1)
            self.export_btn.disabled = False
            if aborted:
                self.status_label.text = "Aborted. Data discarded."
                self.data_buffer = []
            else:
                self.save_buffer_to_sqlite()

        def save_buffer_to_sqlite(self):
            if not self.data_buffer: return
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.executemany('''INSERT INTO sensor_logs (session_id, timestamp, activity_label, device_orientation, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', self.data_buffer)
                conn.commit()
                conn.close()
                self.status_label.text = f"Saved {len(self.data_buffer)} rows to SQLite!"
                self.data_buffer = []
                self.update_session_count()
            except Exception as e:
                self.status_label.text = "DB Save Failed!"

        def export_to_csv(self, instance):
            if platform == 'android':
                from android.storage import primary_external_storage_path
                export_path = os.path.join(primary_external_storage_path(), 'Download', 'sensor_data.csv')
            else:
                export_path = "sensor_data.csv"
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT session_id, timestamp, activity_label, device_orientation, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z FROM sensor_logs")
                rows = cursor.fetchall()
                conn.close()
                if not rows:
                    self.status_label.text = "DB is empty! Nothing to export."
                    return
                with open(export_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['session_id', 'timestamp', 'label', 'device_orientation', 'accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z'])
                    writer.writerows(rows)
                self.status_label.text = f"Saved to Downloads!"
            except Exception as e:
                self.status_label.text = "CSV Export Failed!"

    class DataCollectorApp(App):
        def build(self):
            return DataCollectorLayout()

    if __name__ == '__main__':
        DataCollectorApp().run()
        
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