import tkinter as tk
from trainer_verbs import start_verb_trainer
from trainer_nouns import start_noun_trainer
from trainer_conjugation import start_conjugation_trainer

def main_menu():
    root = tk.Tk()
    root.title("Italienisch Trainer – Hauptmenü")

    tk.Label(root, text="Wähle einen Modus:", font=("Helvetica", 16)).pack(pady=20)

    tk.Button(root, text="1. Vokabeltrainer – Verben", width=30, command=lambda: start_verb_trainer(root)).pack(pady=10)
    tk.Button(root, text="2. Vokabeltrainer – Substantive", width=30, command=lambda: start_noun_trainer(root)).pack(pady=10)
    tk.Button(root, text="3. Konjugationstrainer", width=30, command=lambda: start_conjugation_trainer(root)).pack(pady=10)

    tk.Button(root, text="Beenden", command=root.quit).pack(pady=30)

    root.mainloop()

if __name__ == "__main__":
    main_menu()
