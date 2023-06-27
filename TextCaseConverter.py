import tkinter as tk
import pyperclip

# Define the function to convert the text to title case
def to_title_case(text):
    return text.title()

# Define the function to convert the text to uppercase
def to_upper_case(text):
    return text.upper()

# Define the function to convert the text to lowercase
def to_lower_case(text):
    return text.lower()

# Define the function to copy the result to the clipboard
def copy_to_clipboard(text):
    pyperclip.copy(text)

# Create the main window
window = tk.Tk()
window.title("Text Case Converter")

# Create the text box for input
input_text = tk.Text(window, height=10, width=50)
input_text.pack()

# Create the radio buttons for selecting the case type
selected_case = tk.StringVar()
title_case_button = tk.Radiobutton(window, text="Title Case", variable=selected_case, value="title")
upper_case_button = tk.Radiobutton(window, text="Upper Case", variable=selected_case, value="upper")
lower_case_button = tk.Radiobutton(window, text="Lower Case", variable=selected_case, value="lower")
title_case_button.pack()
upper_case_button.pack()
lower_case_button.pack()

# Create the button for converting the text
convert_button = tk.Button(window, text="Convert", command=lambda: convert_text())
convert_button.pack()

# Create the function to convert the text based on the selected case type
def convert_text():
    text = input_text.get("1.0", "end-1c")
    case_type = selected_case.get()
    if case_type == "title":
        converted_text = to_title_case(text)
    elif case_type == "upper":
        converted_text = to_upper_case(text)
    else:
        converted_text = to_lower_case(text)
    copy_to_clipboard(converted_text)
    result_label.config(text="Result: " + converted_text)
    copy_button.config(state="normal")

# Create the label to show the result
result_label = tk.Label(window, text="Result: ")
result_label.pack()

# Create the button for copying the result to the clipboard
copy_button = tk.Button(window, text="Copy to Clipboard", state="disabled", command=lambda: copy_to_clipboard(result_label.cget("text")[8:]))
copy_button.pack()

# Run the main loop
window.mainloop()
