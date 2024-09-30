# This script calculates the current week's Monday and Friday dates, 
# displays them in a Tkinter window, and allows the user to copy the date range to the clipboard.


import datetime
import tkinter as tk
import tkinter.messagebox as messagebox

# Get the current date
today = datetime.date.today()

# Calculate the date of next Monday
next_week_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)

# Calculate the date of next Friday
next_week_friday = next_week_monday + datetime.timedelta(days=4)

# Format the dates as Month day number, year
next_week_monday_str = next_week_monday.strftime("%B %d, %Y")
next_week_friday_str = next_week_friday.strftime("%B %d, %Y")
date_range_str = f"{next_week_monday_str}, to {next_week_friday_str}"

# Create a Tkinter window to display the dates
root = tk.Tk()
root.title("Dates")
root.geometry("300x150")

# Create a label to display the dates
label = tk.Label(root, text=date_range_str)
label.pack(pady=20)

# Create a button to copy the date range to the clipboard
def copy_to_clipboard():
    root.clipboard_clear()
    root.clipboard_append(date_range_str)
    messagebox.showinfo("Copied", "Date range copied to clipboard!")
    
copy_button = tk.Button(root, text="Copy", command=copy_to_clipboard)
copy_button.pack()

# Run the Tkinter main loop until the user presses Enter
root.bind("<Return>", lambda event: root.quit())
root.mainloop()
