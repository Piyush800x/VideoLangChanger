from threading import Thread
from tkinter import Tk, Toplevel, Label, HORIZONTAL
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Button, Entry, Progressbar
from processor import job

video_path = str
processbar = 0
global progress


def read_file():
    global video_path, progress
    file = askopenfilename(filetypes=[("Video Files", ["*.mp4", "*.avi", "*.mkv"])])
    if file:
        video_path = file
    print("Progress Started!")
    Thread(target=job, args=(progress, file)).start()


def main_window():
    root: Tk = Tk()
    root.geometry("480x360")
    root.title("VideoLangChanger")

    label1: Label = Label(root, text="Choose video")
    label1.pack()

    button1: Button = Button(root, text="Choose", command=lambda: [t1.start(), t2.start()])
    button1.pack()

    root.mainloop()


def processbar_window():
    global progress
    top: Toplevel = Toplevel()
    top.title("VideoLangChanger")
    top.geometry("350x180")
    top.attributes("-topmost", True)

    progress = Progressbar(top, orient=HORIZONTAL, length=200, mode="determinate")

    progress['value'] = 0
    progress.pack(pady=50)

    btn1: Button = Button(top, text="Close", command=top.destroy)
    btn1.pack(pady=10)

    top.mainloop()


t1 = Thread(target=read_file)
t2 = Thread(target=processbar_window)


def main():
    main_window()


if __name__ == '__main__':
    main()
