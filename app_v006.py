import tkinter as tk
import random
from tkinter import messagebox, filedialog
import os
import json
import time

LECTURES_DIR = "lectures"

# --- Spaced Repetition System ---
class SRS:
    def __init__(self):
        self.progress_file = "srs_progress.json"
        self.progress = self.load_progress()

    def save_progress(self):
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, indent=2)

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
        record["due"] = now + record["interval"] * 86400  # one day = 86400 seconds
        self.progress[word] = record

# --- Vocab Trainer App ---
class VocabTrainer:
    def __init__(self, root):
        self.root = root
        self.root.title("Italian Vocabulary Trainer")
        self.reverse = False
        self.conjugation_mode = False

        self.srs = SRS()
        self.lectures = self.load_lectures()
        self.current_lecture_name = tk.StringVar()
        self.current_lecture_name.set(list(self.lectures.keys())[0])
        self.vocab = self.lectures[self.current_lecture_name.get()]

        self.word_history = []
        self.history_index = -1
        self.current_word = None
        self.current_subject = None

        tk.OptionMenu(root, self.current_lecture_name, *self.lectures.keys(), command=self.select_lecture).pack()
        self.direction_button = tk.Button(root, text="Switch to German → Italian", command=self.toggle_direction)
        self.direction_button.pack()

        self.conjugation_button = tk.Button(root, text="Toggle Conjugation Mode", command=self.toggle_conjugation)
        self.conjugation_button.pack()

        self.word_label = tk.Label(root, text="", font=("Helvetica", 20))
        self.word_label.pack(pady=20)

        self.entry = tk.Entry(root, font=("Helvetica", 16))
        self.entry.pack()
        self.entry.bind('<Return>', self.check_answer)
        self.entry.bind('<Right>', self.next_word)
        self.entry.bind('<Left>', self.previous_word)

        self.feedback_label = tk.Label(root, text="", font=("Helvetica", 14))
        self.feedback_label.pack()

        tk.Button(root, text="Next", command=self.next_word).pack()
        tk.Button(root, text="Show Stats", command=self.show_stats).pack()
        tk.Button(root, text="Load New Lecture", command=self.load_new_words).pack()

        self.next_word()

    def load_lectures(self):
        lectures = {}
        if not os.path.exists(LECTURES_DIR):
            os.makedirs(LECTURES_DIR)
        for filename in os.listdir(LECTURES_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(LECTURES_DIR, filename), "r", encoding="utf-8") as f:
                    name = os.path.splitext(filename)[0]
                    lectures[name] = json.load(f)
        return lectures

    def select_lecture(self, _):
        self.vocab = self.lectures[self.current_lecture_name.get()]
        self.word_history.clear()
        self.history_index = -1
        self.next_word()

    def toggle_direction(self):
        self.reverse = not self.reverse
        self.direction_button.config(
            text=f"Switch to {'Italian → German' if self.reverse else 'German → Italian'}"
        )
        self.next_word()

    def toggle_conjugation(self):
        self.conjugation_mode = not self.conjugation_mode
        self.next_word()

    def next_word(self, event=None):
        self.entry.delete(0, tk.END)
        self.feedback_label.config(text="")

        if self.conjugation_mode and "conjugation" in next(iter(self.vocab.values())):
            verb = random.choice(list(self.vocab.keys()))
            subject = random.choice(["io", "tu", "lui/lei", "noi", "voi", "loro"])
            self.current_word = verb
            self.current_subject = subject
            self.word_label.config(text=f"{subject} + {verb}")
        else:
            choices = list(self.vocab.keys()) if not self.reverse else list(self.vocab.values())
            due_words = [w for w in choices if self.srs.get_interval(w)]
            if not due_words:
                due_words = choices
            self.current_word = random.choice(due_words)
            self.word_label.config(text=self.current_word)

        self.word_history.append(self.current_word)
        self.history_index = len(self.word_history) - 1

    def previous_word(self, event=None):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_word = self.word_history[self.history_index]
            self.word_label.config(text=self.current_word)
            self.entry.delete(0, tk.END)
            self.feedback_label.config(text="")

    def check_answer(self, event=None):
        answer = self.entry.get().strip().lower()

        if self.conjugation_mode:
            correct = self.vocab[self.current_word]["conjugation"].get(self.current_subject, "").lower()
            key = f"{self.current_subject} {self.current_word}"
        elif not self.reverse:
            correct = self.vocab[self.current_word].lower() if isinstance(self.vocab[self.current_word], str) else self.vocab[self.current_word]["german"].lower()
            key = self.current_word
        else:
            correct = ""
            key = ""
            for k, v in self.vocab.items():
                val = v if isinstance(v, str) else v.get("german", "")
                if val.lower() == self.current_word.lower():
                    correct = k.lower()
                    key = val
                    break

        if answer == correct:
            self.feedback_label.config(text="✅ Corretto!", fg="green")
            self.srs.update(key, True)
        else:
            self.feedback_label.config(text=f"❌ Sbagliato. Corretto: {correct}", fg="red")
            self.srs.update(key, False)

        self.srs.save_progress()

    def show_stats(self):
        stats = self.srs.progress
        if not stats:
            messagebox.showinfo("Stats", "No progress recorded yet.")
            return
        lines = []
        for word, data in sorted(stats.items(), key=lambda x: x[1]["interval"], reverse=True):
            due_in = int((data["due"] - time.time()) / 86400)
            lines.append(f"{word}: interval={data['interval']} days, ease={round(data['ease'], 2)}, due in {due_in}d")
        messagebox.showinfo("Progress Stats", "\n".join(lines[:30]))

    def load_new_words(self):
        filepath = filedialog.askopenfilename(
            title="Select a JSON file",
            filetypes=[("JSON Files", "*.json")]
        )
        if not filepath:
            return
        try:
            name = os.path.splitext(os.path.basename(filepath))[0]
            with open(filepath, "r", encoding="utf-8") as f:
                new_vocab = json.load(f)
            self.lectures[name] = new_vocab
            self.current_lecture_name.set(name)
            self.select_lecture(name)
            messagebox.showinfo("Success", f"Lecture '{name}' loaded.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = VocabTrainer(root)
    root.mainloop()
