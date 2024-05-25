import sys
from threading import Thread, Event
from tkinter import Tk, Toplevel, Label, HORIZONTAL, messagebox, StringVar
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Button, Entry, Progressbar, Combobox
from processor import job

video_path = None
processbar = 0
global progress
stop_event = Event()
audio_type = None


def read_file():
    global video_path, progress
    file = askopenfilename(filetypes=[("Video Files", ["*.mp4", "*.avi", "*.mkv"])])
    print(file)
    if not file:
        res = messagebox.askretrycancel("VideoLangChanger", "Select a valid video file.")
        if res is False:
            sys.exit(0)
        else:
            return read_file()
    if file:
        video_path = file
    print("Progress Started!")
    job_thread = Thread(target=job, args=(progress, video_path, audio_type))
    job_thread.start()
    job_thread.join()  # Ensure the job thread completes

    # Monitor stop event
    while not stop_event.is_set():
        pass
    print("read_file thread stopping...")
    sys.exit(0)


def main_window():
    root: Tk = Tk()
    root.geometry("380x200")
    root.title("VideoLangChanger")
    root.iconbitmap("logo.ico")

    audio_type_var: StringVar = StringVar()

    label2: Label = Label(root, text="Audio voice")
    label2.grid(row=0, column=0, pady=10, padx=10)
    label1: Label = Label(root, text="Choose video")
    label1.grid(row=0, column=1, pady=10, padx=10)

    def read_vars():
        global audio_type
        audio_type = audio_type_var.get()

    button1: Button = Button(root, text="Choose", command=lambda: [read_vars(), t1.start(), t2.start()])
    button1.grid(row=1, column=1, padx=10)
    cbox: Combobox = Combobox(root, width=15, textvariable=audio_type_var)
    cbox["values"] = ("Male (Hindi)", "Female (Hindi)", "Male (Bengali)", "Female (Bengali)")
    cbox.current(0)
    cbox.grid(row=1, column=0, padx=10)

    root.mainloop()


def processbar_window():
    global progress
    top: Toplevel = Toplevel()
    top.title("VideoLangChanger")
    top.geometry("350x180")
    top.attributes("-topmost", True)
    top.iconbitmap("logo.ico")
    top.protocol("WM_DELETE_WINDOW", full_exit)

    progress = Progressbar(top, orient=HORIZONTAL, length=200, mode="determinate")

    progress['value'] = 0
    progress.pack(pady=50)

    btn1: Button = Button(top, text="Close", command=full_exit)
    btn1.pack(pady=10)

    top.mainloop()


def full_exit():
    res = messagebox.askyesno("VideoLangChanger", "Do you sure want to close this process?")
    if res:
        stop_event.set()  # Signal threads to stop
        sys.exit(1)
    else:
        pass


t1 = Thread(target=read_file)
t2 = Thread(target=processbar_window)


def main():
    main_window()


if __name__ == '__main__':
    main()
