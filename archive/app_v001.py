import tkinter as tk
import random
from tkinter import messagebox
import os

# --- Vocabulary Lectures ---
lectures = {
    "Lecture 1 – 100 Verbs": {
        "essere": "sein", "avere": "haben", "fare": "machen", "dire": "sagen", "potere": "können",
        "andare": "gehen", "vedere": "sehen", "dare": "geben", "sapere": "wissen", "volere": "wollen",
        "dovere": "müssen", "parlare": "sprechen", "trovare": "finden", "lasciare": "lassen", "prendere": "nehmen",
        "mettere": "stellen", "pensare": "denken", "sentire": "hören", "portare": "tragen", "arrivare": "ankommen",
        "credere": "glauben", "tenere": "halten", "guardare": "anschauen", "cominciare": "beginnen", "vivere": "leben",
        "finire": "beenden", "capire": "verstehen", "chiedere": "fragen", "entrare": "eintreten", "lavorare": "arbeiten",
        "scrivere": "schreiben", "mangiare": "essen", "giocare": "spielen", "studiare": "studieren", "aprire": "öffnen",
        "chiudere": "schließen", "correre": "laufen", "camminare": "gehen", "comprare": "kaufen", "pagare": "bezahlen",
        "alzarsi": "aufstehen", "sedersi": "sich setzen", "vestirsi": "sich anziehen", "lavarsi": "sich waschen", "ricordare": "erinnern",
        "dormire": "schlafen", "guidare": "fahren", "telefonare": "anrufen", "usare": "benutzen", "provare": "versuchen",
        "perdere": "verlieren", "vincere": "gewinnen", "cercare": "suchen", "seguire": "folgen",
        "restare": "bleiben", "salire": "einsteigen", "scendere": "aussteigen", "costruire": "bauen", "spiegare": "erklären",
        "rispondere": "antworten", "scegliere": "wählen", "piacere": "gefallen", "succedere": "geschehen", "incontrare": "treffen",
        "diventare": "werden", "nascere": "geboren werden", "morire": "sterben", "rinascere": "wiedergeboren werden", "inviare": "senden",
        "ricevere": "empfangen", "fermare": "anhalten", "spingere": "drücken",
        "tirare": "ziehen", "funzionare": "funktionieren", "cambiare": "wechseln", "contare": "zählen", "costare": "kosten",
        "accendere": "einschalten", "spegnere": "ausschalten", "imparare": "lernen", "insegnare": "unterrichten", "lavare": "waschen",
        "ascoltare": "zuhören", "preparare": "vorbereiten", "ripetere": "wiederholen", "tradurre": "übersetzen", "pulire": "putzen",
        "muovere": "bewegen", "giungere": "erreichen", "volare": "fliegen", "piangere": "weinen", "ridere": "lachen"
    }
}

class VocabTrainer:
    def __init__(self, root):
        self.root = root
        self.root.title("Italian-German Vocabulary Trainer")

        self.reverse = False
        self.word_history = []
        self.history_index = -1

        self.current_lecture = tk.StringVar()
        self.current_lecture.set("Lecture 1 – 100 Verbs")
        self.vocab = lectures[self.current_lecture.get()]
        self.word_weights = {word: 1 for word in self.vocab}

        lecture_menu = tk.OptionMenu(root, self.current_lecture, *lectures.keys(), command=self.select_lecture)
        lecture_menu.pack(pady=5)

        self.word_label = tk.Label(root, text="", font=("Helvetica", 20))
        self.word_label.pack(pady=20)

        self.entry = tk.Entry(root, font=("Helvetica", 16))
        self.entry.pack(pady=10)
        self.entry.bind('<Return>', self.check_answer)
        self.entry.bind('<Right>', self.next_word)
        self.entry.bind('<Left>', self.previous_word)

        self.feedback_label = tk.Label(root, text="", font=("Helvetica", 14))
        self.feedback_label.pack(pady=10)

        self.next_button = tk.Button(root, text="Next", command=self.next_word)
        self.next_button.pack(pady=10)

        self.menu_button = tk.Button(root, text="Load New Words", command=self.load_new_words)
        self.menu_button.pack(pady=10)

        self.direction_button = tk.Button(root, text="Switch to German → Italian", command=self.toggle_direction)
        self.direction_button.pack(pady=10)

        self.current_word = None
        self.next_word()

    def select_lecture(self, _):
        self.vocab = lectures[self.current_lecture.get()]
        self.word_weights = {word: 1 for word in self.vocab}
        self.word_history.clear()
        self.history_index = -1
        self.next_word()

    def toggle_direction(self):
        self.reverse = not self.reverse
        self.direction_button.config(text=f"Switch to {'Italian → German' if self.reverse else 'German → Italian'}")
        self.next_word()

    def weighted_choice(self):
        choices = list(self.vocab.keys()) if not self.reverse else list(self.vocab.values())
        weights = [self.word_weights.get(word, 1) for word in choices]
        return random.choices(choices, weights=weights, k=1)[0]

    def next_word(self, event=None):
        self.entry.delete(0, tk.END)
        self.feedback_label.config(text="")
        self.current_word = self.weighted_choice()
        self.word_history.append(self.current_word)
        self.history_index = len(self.word_history) - 1
        self.word_label.config(text=self.current_word)

    def previous_word(self, event=None):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_word = self.word_history[self.history_index]
            self.word_label.config(text=self.current_word)
            self.entry.delete(0, tk.END)
            self.feedback_label.config(text="")

    def check_answer(self, event=None):
        answer = self.entry.get().strip().lower()
        if not self.reverse:
            correct = self.vocab[self.current_word].lower()
        else:
            correct = [k for k, v in self.vocab.items() if v == self.current_word]
            correct = correct[0].lower() if correct else ""

        if answer == correct:
            self.feedback_label.config(text="✅ Corretto!", fg="green")
            self.word_weights[self.current_word] = max(1, self.word_weights.get(self.current_word, 1) - 1)
        else:
            self.feedback_label.config(text=f"❌ Sbagliato. Corretto: {correct}", fg="red")
            self.word_weights[self.current_word] = self.word_weights.get(self.current_word, 1) + 2

    def load_new_words(self):
        filepath = tk.filedialog.askopenfilename(
            title="Select a text file",
            filetypes=[("Text Files", "*.txt")]
        )
        if not filepath:
            return
        try:
            new_lecture_name = os.path.basename(filepath).split('.')[0]
            new_vocab = {}
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if ":" in line:
                        ita, ger = line.strip().split(":")
                        new_vocab[ita.strip()] = ger.strip()
            lectures[new_lecture_name] = new_vocab
            menu = self.root.nametowidget(self.current_lecture._name)
            menu['menu'].add_command(label=new_lecture_name, command=tk._setit(self.current_lecture, new_lecture_name, self.select_lecture))
            messagebox.showinfo("Parole caricate", f"Lezione '{new_lecture_name}' caricata con successo!")
        except Exception as e:
            messagebox.showerror("Errore", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = VocabTrainer(root)
    root.mainloop()
