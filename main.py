import customtkinter
import tkinter
from threading import Thread

from helper import read_json
from helper import write_json

from transcribe import generate_transcript

render_queue = []
transcribe_list_json = "transcribeList.json"

class ScrollableLabelButtonFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.command = command
        self.radiobutton_variable = customtkinter.StringVar()
        self.label_list = []
        self.button_list = []

    def add_item(self, item, image=None):
        label = customtkinter.CTkLabel(self, text=item, image=image, compound="right", padx=5, anchor="e", font=("Roboto", 10), width=100)
        button = customtkinter.CTkButton(self, text="Remove", width=80, height=24)
        if self.command is not None:
            button.configure(command=lambda: self.command(item))
        label.grid(row=len(self.label_list), column=0, pady=(0, 10), sticky="w")
        button.grid(row=len(self.button_list), column=1, pady=(0, 10), padx=5)
        self.label_list.append(label)
        self.button_list.append(button)

    def remove_item(self, item):
        for label, button in zip(self.label_list, self.button_list):
            if item == label.cget("text"):
                label.destroy()
                button.destroy()
                self.label_list.remove(label)
                self.button_list.remove(button)
                return

class App(customtkinter.CTk):

    def __init__(self):
        super().__init__()
        self.title("Transcript Generator")
        self.iconbitmap("N.ico")

        self.transcribe_thread = False


        self.grid_rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        row01 = customtkinter.CTkFrame(master=self)
        row01.grid_rowconfigure(0, weight=1)
        row01.columnconfigure(0, weight=1)
        row01.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        frame = customtkinter.CTkFrame(master=row01)
        frame.grid(row=0, column=0, padx=0, pady=0, sticky="n")

        button = customtkinter.CTkButton(master=frame, text="Get Files", command=self.filenames_function)
        button.grid(pady=20, padx=10)

        self.deepl_label = customtkinter.CTkLabel(master=frame, text="Deepl Key", font=("Roboto", 14))
        self.deepl_label.grid(pady=(10,0), padx=10)

        self.deeplKey_entry = customtkinter.CTkEntry(master=frame, placeholder_text="Your Deepl API Key")
        self.deeplKey_entry.grid(pady=(10,20), padx=10)

        row02 = customtkinter.CTkFrame(master=self)
        row02.grid_rowconfigure(0, weight=1)
        row02.columnconfigure(4, weight=1)
        row02.grid(row=1, column=0, padx=20, pady=(10,0), sticky="w")

        self.label_queue = customtkinter.CTkLabel(master=row02, text="Transcribe Queue: 0 Clips", font=("Roboto", 14))
        self.label_queue.grid(row=0, column= 0, pady=12, padx=10)

        self.transcribe_button = customtkinter.CTkButton(master=row02, text="Transcribe", command=self.transcribe_button_action)
        self.transcribe_button.grid(row=0, column=1,pady=20, padx=10)

        self.language_entry = customtkinter.CTkEntry(master=row02, placeholder_text="language")
        self.language_entry.grid(row=0, column=2,pady=20, padx=10)

        self.generate_docx = tkinter.BooleanVar(self.master, False)
        self.check_docx = customtkinter.CTkCheckBox(master=row02, text="Generate Docx", variable=self.generate_docx, onvalue=True, offvalue=False)
        self.check_docx.grid(row=0, column=3, pady=12, padx=10)

        self.deepl_translate = tkinter.BooleanVar(self.master, False)
        self.check_deepl = customtkinter.CTkCheckBox(master=row02, text="Translate", variable=self.deepl_translate, onvalue=True, offvalue=False)
        self.check_deepl.grid(row=0, column=4, pady=12, padx=10)

        self.transcribe_list = ScrollableLabelButtonFrame(master=self, width=800, command=self.label_button_frame_event, corner_radius=0)
        self.transcribe_list.grid(row=2, column=0, padx=20, pady=(5,20), sticky="s")


    def add_job(self, file, cache=True):
        render_queue.append(file)
        self.transcribe_list.add_item(file)
        if cache:
            self.add_to_cache(file)
        self.label_queue.configure(text="Transcribe Queue: " + str(len(render_queue)) +" Clips" )

    def remove_job(self, file):
        render_queue.remove(file)
        self.transcribe_list.remove_item(file)
        self.remove_from_cache(file)
        self.label_queue.configure(text="Transcribe Queue: " + str(len(render_queue)) +" Clips" )

    def label_button_frame_event(self, item):
        print(f"label button frame clicked: {item}")
        self.remove_job(item)

    def filenames_function(self):
        files = tkinter.filedialog.askopenfilenames()
        for f in files:
            self.add_job(f)
        print(render_queue)


    def read_cache(self):
        cache_tasks = read_json(transcribe_list_json)
        for task in cache_tasks:
            self.add_job(task, False)

    def add_to_cache(self, job):
        cache_tasks = read_json(transcribe_list_json)
        cache_tasks.append(job)
        write_json(cache_tasks, transcribe_list_json)
    
    def remove_from_cache(self, job):
        cache_tasks = read_json(transcribe_list_json)
        cache_tasks.remove(job)
        write_json(cache_tasks, transcribe_list_json)
        self.transcribe_list.remove_item(job)

    def transcribe_button_action(self):
        if self.transcribe_thread == True:
            self.transcribe_thread = False
            transcribe_button = self.transcribe_button
            transcribe_button.configure(state="disabled")
        else:
            self.transcribe()


    def transcribe(self):
        thread = Thread(target=self.transcribing)
        self.transcribe_thread = True
        thread.start()

    def transcribing(self):
        transcribe_button = self.transcribe_button
        transcribe_button.configure(text="Stop")

        while len(render_queue) > 0 and self.transcribe_thread:
            video = render_queue[0]
            print("TRANSCRIBING - "+ video)
            button = self.transcribe_list.button_list[0]
            button.configure(state="disabled")
            button.configure(text="Transcribing")
            generate_transcript(sourcefile=video,lang=self.language_entry.get(),complex=False, createDOCX=self.generate_docx.get(),speakerDiarization=True, translate=self.deepl_translate.get(), deeplKey=self.deeplKey_entry.get())
            self.remove_job(video)

        transcribe_button.configure(text="Transcribe")
        transcribe_button.configure(state="normal")
        self.transcribe_thread = False

if __name__ == "__main__":
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    app = App()
    app.mainloop()