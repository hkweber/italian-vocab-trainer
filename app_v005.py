import tkinter as tk
import random
from tkinter import messagebox, filedialog
import os
import json
import time
from datetime import datetime

LECTURE_FOLDER = "lectures"

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

        self.lectures = self.load_lectures()
        self.reverse = False
        self.word_history = []
        self.history_index = -1
        self.srs = SRS()

        self.current_lecture = tk.StringVar()
        lecture_names = list(self.lectures.keys())
        if lecture_names:
            self.current_lecture.set(lecture_names[0])
        self.vocab = self.lectures.get(self.current_lecture.get(), {})

        self.create_widgets()
        self.next_word()

    def load_lectures(self):
        lectures = {}
        if not os.path.exists(LECTURE_FOLDER):
            os.makedirs(LECTURE_FOLDER)
        for filename in os.listdir(LECTURE_FOLDER):
            if filename.endswith(".json"):
                path = os.path.join(LECTURE_FOLDER, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        lectures.update(data)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        return lectures

    def create_widgets(self):
        tk.OptionMenu(self.root, self.current_lecture, *self.lectures.keys(), command=self.select_lecture).pack(pady=5)

        self.word_label = tk.Label(self.root, text="", font=("Helvetica", 20))
        self.word_label.pack(pady=20)

        self.entry = tk.Entry(self.root, font=("Helvetica", 16))
        self.entry.pack(pady=10)
        self.entry.bind('<Return>', self.check_answer)
        self.entry.bind('<Right>', self.next_word)
        self.entry.bind('<Left>', self.previous_word)

        self.feedback_label = tk.Label(self.root, text="", font=("Helvetica", 14))
        self.feedback_label.pack(pady=10)

        tk.Button(self.root, text="Next", command=self.next_word).pack(pady=10)
        tk.Button(self.root, text="Load New Words", command=self.load_new_words).pack(pady=10)
        tk.Button(self.root, text="Switch to German → Italian", command=self.toggle_direction).pack(pady=10)
        tk.Button(self.root, text="Show Stats", command=self.show_stats).pack(pady=10)

    def select_lecture(self, _=None):
        self.vocab = self.lectures.get(self.current_lecture.get(), {})
        self.word_history.clear()
        self.history_index = -1
        self.next_word()

    def toggle_direction(self):
        self.reverse = not self.reverse
        direction = "German → Italian" if self.reverse else "Italian → German"
        self.root.children["!button2"].config(text=f"Switch to {direction}")
        self.next_word()

    def next_word(self, event=None):
        self.entry.delete(0, tk.END)
        self.feedback_label.config(text="")

        choices = list(self.vocab.values()) if self.reverse else list(self.vocab.keys())
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
            return self.vocab.get(self.current_word, "").lower()
        else:
            reverse_map = {v.lower(): k.lower() for k, v in self.vocab.items()}
            return reverse_map.get(self.current_word.lower(), "")

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

    def show_stats(self):
        stats = self.srs.progress
        if not stats:
            messagebox.showinfo("Stats", "No progress recorded yet.")
            return

        lines = []
        for word, data in sorted(stats.items(), key=lambda x: x[1]['interval'], reverse=True):
            due_in_days = int((data["due"] - time.time()) / 86400)
            due_str = f"{due_in_days} days" if due_in_days > 0 else "due now"
            lines.append(f"{word}: interval={data['interval']}, ease={round(data['ease'], 2)}, due in {due_str}")

        messagebox.showinfo("Progress Stats", "\n".join(lines[:30]))

    def load_new_words(self):
        filepath = filedialog.askopenfilename(
            title="Select a JSON file",
            filetypes=[("JSON Files", "*.json")]
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.lectures.update(data)
                for name in data:
                    self.root.children["!optionmenu"]["menu"].add_command(
                        label=name,
                        command=tk._setit(self.current_lecture, name, self.select_lecture)
                    )
            messagebox.showinfo("Parole caricate", "Nuova lezione caricata con successo!")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = VocabTrainer(root)
    root.mainloop()
