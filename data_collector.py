import time
import csv
import win32gui
import math
import platform
import subprocess
import shutil
import os
import zipfile
from pynput.mouse import Listener, Controller
from pynput.keyboard import Listener as KeyboardListener, Key
from PIL import ImageGrab
import ftplib

# Global variables
game_window_titles = ["Old School RuneScape", "Runelite"]  # Update with the actual game window titles
is_game_open = False
last_move_time = None
afk_start_time = None
mouse_positions = []
mouse_clicks = []
keyboard_inputs = []
start_time = time.time()

# Player statistics
total_actions = 0

# FTP server credentials
ftp_host = 'ftp.example.com'
ftp_username = 'your_username'
ftp_password = 'your_password'
remote_directory = 'path/to/remote/folder/'

# Mouse speed calculation variables
last_mouse_position = None
last_mouse_time = None

# Callback function for mouse movements
def on_move(x, y):
    global is_game_open, last_move_time, afk_start_time, mouse_positions, last_mouse_position, last_mouse_time

    # Check if the game is open
    if not is_game_open:
        if any(title in win32gui.GetWindowText(win32gui.GetForegroundWindow()) for title in game_window_titles):
            is_game_open = True

    # Record delay between movements
    if is_game_open:
        if last_move_time is not None:
            delay = time.time() - last_move_time
            mouse_positions.append(delay)
        last_move_time = time.time()

    # Calculate mouse speed
    current_time = time.time()
    if last_mouse_position is not None and last_mouse_time is not None:
        distance = math.sqrt((x - last_mouse_position[0])**2 + (y - last_mouse_position[1])**2)
        time_diff = current_time - last_mouse_time
        speed = distance / time_diff
        # Add mouse speed to the data list
        mouse_positions.append(speed)
    last_mouse_position = (x, y)
    last_mouse_time = current_time

    # Record AFK time
    if is_game_open:
        if afk_start_time is None:
            afk_start_time = time.time()
        else:
            afk_time = time.time() - afk_start_time
            mouse_positions.append(afk_time)
            afk_start_time = None

# Callback function for mouse clicks
def on_click(x, y, button, pressed):
    global is_game_open, mouse_clicks

    # Check if the game is open
    if not is_game_open:
        if any(title in win32gui.GetWindowText(win32gui.GetForegroundWindow()) for title in game_window_titles):
            is_game_open = True

    # Record mouse clicks
    if is_game_open:
        if pressed:
            mouse_clicks.append(button)

# Callback function for keyboard inputs
def on_press(key):
    global is_game_open, keyboard_inputs

    # Check if the game is open
    if not is_game_open:
        if any(title in win32gui.GetWindowText(win32gui.GetForegroundWindow()) for title in game_window_titles):
            is_game_open = True

    # Record keyboard inputs
    if is_game_open:
        keyboard_inputs.append(key)

# Callback function for keyboard inputs
def on_release(key):
    global is_game_open, keyboard_inputs

    # Check if the game is open
    if not is_game_open:
        if any(title in win32gui.GetWindowText(win32gui.GetForegroundWindow()) for title in game_window_titles):
            is_game_open = True

    # Record keyboard inputs
    if is_game_open:
        keyboard_inputs.append(key)

# Function to write data to CSV file
def write_to_csv(data):
    global remote_directory

    # Generate a unique file name using timestamp
    timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    file_name = f"data_{timestamp}.csv"
    file_path = os.path.join(os.getcwd(), file_name)
    remote_path = os.path.join(remote_directory, file_name)

    # Open CSV file in write mode
    with open(file_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(data)

    return file_path, remote_path

# Function to upload file to FTP server
def upload_to_ftp(file_path, remote_path):
    try:
        with ftplib.FTP(ftp_host) as ftp:
            ftp.login(ftp_username, ftp_password)
            with open(file_path, 'rb') as file:
                ftp.storbinary('STOR ' + remote_path, file)
            print('File uploaded to FTP server successfully.')
    except Exception as e:
        print('Error uploading file to FTP server:', str(e))

# Main script
def main():
    global is_game_open, mouse_positions, mouse_clicks, keyboard_inputs, start_time

    # Set up mouse listener
    mouse_listener = Listener(on_move=on_move, on_click=on_click)
    mouse_listener.start()

    # Set up keyboard listener
    keyboard_listener = KeyboardListener(on_press=on_press, on_release=on_release)
    keyboard_listener.start()

    # Wait for the listeners to start
    time.sleep(1)

    while True:
        # Check if the game is open
        if not is_game_open:
            if any(title in win32gui.GetWindowText(win32gui.GetForegroundWindow()) for title in game_window_titles):
                is_game_open = True

        # Check if it's time to send the email (every 1 hour)
        current_time = time.time()
        elapsed_time = current_time - start_time
        if elapsed_time >= 3600:  # 1 hour = 60 minutes * 60 seconds = 3600 seconds
            # Write data to CSV file
            data = [elapsed_time] + mouse_positions + mouse_clicks + keyboard_inputs
            file_path, remote_path = write_to_csv(data)

            # Upload CSV file to FTP server
            upload_to_ftp(file_path, remote_path)

            # Reset variables
            start_time = current_time
            mouse_positions = []
            mouse_clicks = []
            keyboard_inputs = []

        time.sleep(1)

if __name__ == '__main__':
    main()
