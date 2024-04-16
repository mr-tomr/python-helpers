# Created by Tom R.
# When running, moves mouse back and forth on screen, preventing screen savers and other applciation timeouts.


import pyautogui
import math

# Get the center of the screen
screen_width, screen_height = pyautogui.size()
center_x, center_y = screen_width / 2, screen_height / 2

# Define the radius and angle step size for the circle
radius = 100
angle_step = 5

# Start the loop to move the mouse in a circle
while not pyautogui.mouseDown():
    # Calculate the current angle in radians
    angle = 0
    while angle < 2 * math.pi:
        # Calculate the x and y coordinates of the current point on the circle
        x = center_x + int(radius * math.cos(angle))
        y = center_y + int(radius * math.sin(angle))
        
        # Move the mouse to the current point on the circle
        pyautogui.moveTo(x, y, duration=0.1)
        
        # Increment the angle by the step size
        angle += angle_step
