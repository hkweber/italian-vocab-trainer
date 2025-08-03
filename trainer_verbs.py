import tkinter as tk

def start_verb_trainer(previous_window):
    previous_window.destroy()
    root = tk.Tk()
    root.title("Vokabeltrainer – Verben")
    tk.Label(root, text="Hier kommt der Verbtrainer hin.").pack(pady=20)
    tk.Button(root, text="Zurück zum Hauptmenü", command=lambda: (root.destroy(), __import__('app').main_menu())).pack(pady=20)
    root.mainloop()
