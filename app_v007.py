import tkinter as tk
import random
from tkinter import messagebox, filedialog
import os
import json
import time

def load_lectures():
    lectures = {}
    for filename in os.listdir("lectures"):
        if filename.endswith(".json"):
            filepath = os.path.join("lectures", filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = json.load(f)
                # validate format
                for word, entry in content.items():
                    if not isinstance(entry, dict) or "de" not in entry:
                        raise ValueError(f"Invalid format in '{filename}': '{word}' is missing 'de'")
                name = os.path.splitext(filename)[0]
                lectures[name] = content
    return lectures


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
        record["due"] = now + record["interval"] * 86400
        self.progress[word] = record


class VocabTrainer:
    def __init__(self, root):
        self.root = root
        self.root.title("Italian-German Vocabulary Trainer")

        self.reverse = False
        self.word_history = []
        self.history_index = -1
        self.current_word = None

        self.srs = SRS()
        self.lectures = load_lectures()

        self.current_lecture = tk.StringVar()
        self.current_lecture.set(list(self.lectures.keys())[0])
        self.vocab = self.lectures[self.current_lecture.get()]

        lecture_menu = tk.OptionMenu(root, self.current_lecture, *self.lectures.keys(), command=self.select_lecture)
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

        tk.Button(root, text="Next", command=self.next_word).pack()
        tk.Button(root, text="Switch to German → Italian", command=self.toggle_direction).pack()
        tk.Button(root, text="Show Stats", command=self.show_stats).pack()
        tk.Button(root, text="Load New Lecture", command=self.load_new_words).pack()

        self.next_word()

    def select_lecture(self, _):
        self.vocab = self.lectures[self.current_lecture.get()]
        self.word_history.clear()
        self.history_index = -1
        self.next_word()

    def toggle_direction(self):
        self.reverse = not self.reverse
        self.next_word()

    def next_word(self, event=None):
        self.entry.delete(0, tk.END)
        self.feedback_label.config(text="")

        choices = list(self.vocab.keys()) if not self.reverse else [v["de"] for v in self.vocab.values()]
        due_words = [w for w in choices if self.srs.get_interval(w)] or choices

        self.current_word = random.choice(due_words)
        self.word_history.append(self.current_word)
        self.history_index = len(self.word_history) - 1

        display = self.vocab[self.current_word]["de"] if self.reverse else self.current_word
        self.word_label.config(text=display)

    def previous_word(self, event=None):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_word = self.word_history[self.history_index]
            display = self.vocab[self.current_word]["de"] if self.reverse else self.current_word
            self.word_label.config(text=display)
            self.entry.delete(0, tk.END)
            self.feedback_label.config(text="")

    def get_correct_answer(self):
        if self.reverse:
            return self.current_word.lower()
        return self.vocab[self.current_word]["de"].lower()

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

        # Optional: show conjugation if available
        conj = self.vocab[self.current_word].get("conjugation")
        if conj:
            text = "\n".join(f"{k}: {v}" for k, v in conj.items())
            messagebox.showinfo("Conjugation", text)

    def show_stats(self):
        stats = self.srs.progress
        if not stats:
            messagebox.showinfo("Stats", "No progress recorded yet.")
            return
        lines = [
            f"{word}: interval={data['interval']} days, ease={round(data['ease'],2)}, due in {int((data['due'] - time.time()) / 86400)}d"
            for word, data in sorted(stats.items(), key=lambda x: x[1]['interval'], reverse=True)
        ]
        messagebox.showinfo("Progress Stats", "\n".join(lines[:30]))

    def load_new_words(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                new_data = json.load(f)
            for word, entry in new_data.items():
                if not isinstance(entry, dict) or "de" not in entry:
                    raise ValueError(f"Invalid entry for '{word}'")
            name = os.path.splitext(os.path.basename(path))[0]
            self.lectures[name] = new_data
            menu = self.root.nametowidget(self.current_lecture._name)
            menu['menu'].add_command(label=name, command=tk._setit(self.current_lecture, name, self.select_lecture))
            messagebox.showinfo("Success", f"Lecture '{name}' loaded.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = VocabTrainer(root)
    root.mainloop()
