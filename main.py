import customtkinter
import tkinter



class App(customtkinter.CTk):

    def __init__(self):
        super().__init__()
        self.title("Transcript Generator")
        self.iconbitmap("N.ico")


if __name__ == "__main__":
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    app = App()
    app.mainloop()