import csv
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
from threading import Lock
import random
import shutil

# Constants
DATA_DIRECTORY = "sensor_data"
FILE_LOCK = Lock()  # Lock to manage file access
SENSOR_DATA_INTERVAL_MS = 1  # Interval to generate sensor data in milliseconds
FILE_WRITE_INTERVAL_MS = 40  # Interval to write data to CSV file in milliseconds
MAX_FILES = 25  # Maximum number of files to cycle through
MAX_DATA_POINTS = 1000  # Maximum number of data points to keep in memory
PLOT_REFRESH_INTERVAL_MS = 100  # Interval to refresh the plot in milliseconds
PLOT_CLEAR_INTERVAL_S = 30  # Interval to clear the plot in seconds


# Function to simulate sensor data generation and write to CSV
def generate_sensor_data():
    # Directory to store generated CSV files
    os.makedirs(DATA_DIRECTORY, exist_ok=True)
    start_time = time.time()
    file_counter = 0
    data_buffer = []
    timestamp = 0

    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time

        # Generate sensor data every SENSOR_DATA_INTERVAL_MS
        if elapsed_time >= SENSOR_DATA_INTERVAL_MS / 1000.0:
            timestamp += 1
            data = {
                "timestamp": timestamp,
                "value": random.random()  # Simulated sensor value
            }
            data_buffer.append(data)
            start_time = current_time

        # Write data to a new CSV file every FILE_WRITE_INTERVAL_MS
        if len(data_buffer) >= FILE_WRITE_INTERVAL_MS:
            filename = f"sensor_data_{file_counter}.csv"
            filepath = os.path.join(DATA_DIRECTORY, filename)
            
            with FILE_LOCK:  # Ensure exclusive access to the file
                with open(filepath, mode='w', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=["timestamp", "value"])
                    writer.writeheader()
                    writer.writerows(data_buffer)

            print(f"Generated file: {filename}")
            data_buffer.clear()
            file_counter = (file_counter + 1) % MAX_FILES  # Cycle through MAX_FILES files

        # Sleep briefly to avoid high CPU usage
        time.sleep(0.0005)

# Function to display data from CSV files
def display_sensor_data():
    # Create a simple Tkinter window
    root = tk.Tk()
    root.title("Real-Time Sensor Data Display")

    fig, ax = plt.subplots(figsize=(12, 6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    start_time = time.time()
    data_queue = deque(maxlen=MAX_DATA_POINTS)  # Limit the number of data points to manage memory

    def update_plot():
        nonlocal start_time
        csv_files = sorted([f for f in os.listdir(DATA_DIRECTORY) if f.endswith('.csv')])

        if csv_files:
            with FILE_LOCK:  # Ensure exclusive access to the files
                for csv_file in csv_files:
                    filepath = os.path.join(DATA_DIRECTORY, csv_file)
                    df = pd.read_csv(filepath)
                    for _, row in df.iterrows():
                        data_queue.append(row)

            if data_queue:
                combined_df = pd.DataFrame(data_queue)
                avg_value = combined_df["value"].mean()
                max_value = combined_df["value"].max()
                min_value = combined_df["value"].min()

                ax.clear()
                ax.plot(combined_df["timestamp"] / 1000, combined_df["value"], label="Sensor Value")  # Convert timestamp to seconds
                ax.axhline(avg_value, color='r', linestyle='--', label=f"Average: {avg_value:.2f}")
                ax.axhline(max_value, color='g', linestyle='--', label=f"Max: {max_value:.2f}")
                ax.axhline(min_value, color='b', linestyle='--', label=f"Min: {min_value:.2f}")

                ax.set_xlabel("Time (s)")
                ax.set_ylabel("Value")
                ax.set_title("Real-Time Sensor Data")
                # ax.legend()

                canvas.draw()

        # Clear the plot and reset data every PLOT_CLEAR_INTERVAL_S to manage memory
        if time.time() - start_time > PLOT_CLEAR_INTERVAL_S:
            ax.clear()
            data_queue.clear()  # Clear the data queue to avoid memory issues
            start_time = time.time()

        root.after(PLOT_REFRESH_INTERVAL_MS, update_plot)

    root.after(PLOT_REFRESH_INTERVAL_MS, update_plot)
    root.mainloop()

if __name__ == "__main__":
    shutil.rmtree(DATA_DIRECTORY)
    # Run the sensor data generation and display concurrently
    from threading import Thread
    Thread(target=generate_sensor_data, daemon=True).start()
    display_sensor_data()
