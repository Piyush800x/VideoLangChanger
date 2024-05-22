from tkinter import Tk, Toplevel, Label
from tkinter.ttk import Button, Entry
from processor import *


if __name__ == '__main__':
    extract_audio()     # Extracts audio from video file
    audio_2_text()      # Convert audio to text and saves it to .json
    clean_data()        # .json to cleaned data as list of dicts
    text_2_audio()      # convert that text to audio
