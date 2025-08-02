import tkinter as tk
import random
from tkinter import messagebox
import os
import json
import time

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

class SRS:
    def __init__(self):
        self.progress_file = "srs_progress.json"
        self.progress = self.load_progress()

    def save_progress(self):
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f)

    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_interval(self, word):
        record = self.progress.get(word, {"interval": 1, "due": 0, "ease": 2.5})
        if time.time() >= record["due"]:
            return record
        return None

    def update(self, word, correct):
        now = time.time()
        record = self.progress.get(word, {"interval": 1, "due": now, "ease": 2.5})
        if correct:
            record["interval"] = max(1, int(record["interval"] * record["ease"]))
            record["ease"] = min(3.0, record["ease"] + 0.1)
        else:
            record["interval"] = 1
            record["ease"] = max(1.3, record["ease"] - 0.2)
        record["due"] = now + record["interval"] * 24 * 60 * 60
        self.progress[word] = record

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

        self.srs = SRS()

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

        self.stats_button = tk.Button(root, text="Show Stats", command=self.show_stats)
        self.stats_button.pack(pady=10)

        self.current_word = None
        self.next_word()

    def select_lecture(self, _):
        self.vocab = lectures[self.current_lecture.get()]
        self.word_history.clear()
        self.history_index = -1
        self.next_word()

    def toggle_direction(self):
        self.reverse = not self.reverse
        self.direction_button.config(text=f"Switch to {'German → Italian' if self.reverse else 'Italian → German'}")
        self.next_word()

    def next_word(self, event=None):
        self.entry.delete(0, tk.END)
        self.feedback_label.config(text="")

        choices = list(self.vocab.keys()) if not self.reverse else list(self.vocab.values())
        due_words = [w for w in choices if self.srs.get_interval(w)]
        if not due_words:
            due_words = choices

        self.current_word = random.choice(due_words)
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

    def get_correct_answer(self):
        if not self.reverse:
            return self.vocab[self.current_word].lower()
        else:
            reverse_map = {v: k for k, v in self.vocab.items()}
            return reverse_map.get(self.current_word, "").lower()

    def check_answer(self, event=None):
        answer = self.entry.get().strip().lower()
        correct = self.get_correct_answer()

        if answer == correct:
            self.feedback_label.config(text="✅ Corretto!", fg="green")
            self.srs.update(self.current_word, True)
        else:
            self.feedback_label.config(text=f"❌ Sbagliato. Corretto: {correct}", fg="red")
            self.srs.update(self.current_word, False)
        self.srs.save_progress()


# (der Anfang bleibt gleich – bis einschließlich show_stats)

    def show_stats(self):
        stats = self.srs.progress
        total = len(stats)
        if total == 0:
            messagebox.showinfo("Stats", "No progress recorded yet.")
            return

        lines = []
        for word, data in sorted(stats.items(), key=lambda x: x[1]['interval'], reverse=True):
            due_in = int((data['due'] - time.time()) / 60 / 60 / 24)
            lines.append(f"{word}: interval={data['interval']} days, ease={round(data['ease'], 2)}, due in {due_in}d")

        messagebox.showinfo("Progress Stats", "\n".join(lines[:30]))

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
                        parts = line.strip().split(":", 1)
                        if len(parts) != 2:
                            continue
                        ita, ger = parts
                        new_vocab[ita.strip()] = ger.strip()
            lectures[new_lecture_name] = new_vocab
            menu = self.root.nametowidget(self.current_lecture._name)
            menu['menu'].add_command(label=new_lecture_name, command=tk._setit(self.current_lecture, new_lecture_name, self.select_lecture))
            messagebox.showinfo("Parole caricate", f"Lezione '{new_lecture_name}' caricata con successo!")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def get_correct_answer(self):
        if not self.reverse:
            return self.vocab[self.current_word].lower()
        else:
            reverse_map = {v: k for k, v in self.vocab.items()}
            return reverse_map.get(self.current_word, "").lower()

    def check_answer(self, event=None):
        answer = self.entry.get().strip().lower()
        correct = self.get_correct_answer()

        if answer == correct:
            self.feedback_label.config(text="✅ Corretto!", fg="green")
            self.srs.update(self.current_word, True)
        else:
            self.feedback_label.config(text=f"❌ Sbagliato. Corretto: {correct}", fg="red")
            self.srs.update(self.current_word, False)

        self.srs.save_progress()

# Der Rest ab main bleibt gleich:
if __name__ == "__main__":
    root = tk.Tk()
    app = VocabTrainer(root)
    root.mainloop()
