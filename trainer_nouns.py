import tkinter as tk
import tkinter.messagebox as messagebox
import random
import os
import json
import time
class SRS:
    def normalize_key(self, text):
        return text.lower().replace("’", "'").strip()
    def __init__(self, filename="srs_nouns.json"):
        self.progress_file = filename
        self.progress = self.load_progress()

    def save_progress(self):
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f)

    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_due_words(self, words):
        words = [self.normalize_key(w) for w in words]
        now = time.time()
        return [
            w for w in words
            if self.progress.get(w, {"due": 0})["due"] <= now
        ]

    def update(self, word, correct):
        word = self.normalize_key(word)
        now = time.time()
        record = self.progress.get(word, {"interval": 1, "due": now, "ease": 2.5})
        if correct:
            record["interval"] = max(1, int(record["interval"] * record["ease"]))
            record["ease"] = min(3.0, record["ease"] + 0.1)
        else:
            record["interval"] = 1
            record["ease"] = max(1.3, record["ease"] - 0.2)
        record["due"] = now + record["interval"] * 86400  # 1 day = 86400 sec
        self.progress[word] = record


def load_lecture_files():
    path = os.path.join("lectures", "nouns")
    files = [f for f in os.listdir(path) if f.endswith(".json")]
    return files

def load_noun_lecture(files):
    data = {}
    for name in files:
        path = os.path.join("lectures", "nouns", name)
        with open(path, "r", encoding="utf-8") as f:
            part = json.load(f)
            for key, value in part.items():
                if isinstance(value, dict) and "de" in value:
                    data[key] = value
    return data

def normalize(text):
    return text.lower().replace("’", "'").strip()

def strip_german_article(text):
    text = normalize(text)
    for article in ["der ", "die ", "das "]:
        if text.startswith(article):
            return text[len(article):]
    return text

srs = SRS()

def start_noun_trainer(previous_window):
    previous_window.destroy()
    root = tk.Tk()
    root.title("Vokabeltrainer – Substantive")

    # State
    selected_files = []
    nouns = {}
    reverse = False
    current_word = None
    word_history = []
    history_index = -1
    stats = {"correct": 0, "wrong": 0}

    # Functions
    def toggle_direction():
        nonlocal reverse
        reverse = not reverse
        direction_button.config(text=f"Richtung: {'Italienisch → Deutsch' if not reverse else 'Deutsch → Italienisch'}")
        next_word()

    def update_selected_lessons():
        nonlocal selected_files, nouns, word_history, history_index
        selected_files = [f for f, var in check_vars.items() if var.get()]
        if not selected_files:
            feedback_label.config(text="⚠️ Keine Lektion ausgewählt", fg="orange")
            return
        nouns.clear()
        nouns.update(load_noun_lecture(selected_files))
        word_history.clear()
        history_index = -1
        next_word()

    def next_word(event=None):
        nonlocal current_word, history_index
        if not nouns:
            feedback_label.config(text="⚠️ Keine Vokabeln geladen", fg="orange")
            return
        entry.delete(0, tk.END)
        feedback_label.config(text="")
        choices = srs.get_due_words(list(nouns.keys())) or list(nouns.keys())
        current_word = random.choice(choices)
        word_history.append(current_word)
        history_index = len(word_history) - 1
        question = current_word if not reverse else nouns[current_word]["de"]
        word_label.config(text=question)

    def previous_word(event=None):
        nonlocal current_word, history_index
        if history_index > 0:
            history_index -= 1
            current_word = word_history[history_index]
            question = current_word if not reverse else nouns[current_word]["de"]
            word_label.config(text=question)
            entry.delete(0, tk.END)
            feedback_label.config(text="")

    def check_answer(event=None):
        answer = normalize(entry.get())
        if not reverse:
            correct = normalize(nouns[current_word]["de"])
            answer_clean = strip_german_article(answer)
            correct_clean = strip_german_article(correct)
        else:
            correct = normalize(current_word)
            answer_clean = answer
            correct_clean = correct

        if answer_clean == correct_clean:
            feedback_label.config(text="✅ Richtig!", fg="green")
            stats["correct"] += 1
            srs.update(current_word, True)
            srs.save_progress()
        else:
            feedback_label.config(text=f"❌ Falsch. Korrekt: {correct}", fg="red")
            stats["wrong"] += 1
            srs.update(current_word, False)
            srs.save_progress()

    def show_stats():
        total = stats["correct"] + stats["wrong"]
        summary = f"Beantwortet: {total}\\n✅ Richtig: {stats['correct']}\\n❌ Falsch: {stats['wrong']}"
        messagebox.showinfo("Statistik", summary)

    # UI Layout
    tk.Label(root, text="Substantiv-Übung", font=("Helvetica", 16)).pack(pady=10)
    direction_button = tk.Button(root, text="Richtung: Italienisch → Deutsch", command=toggle_direction)
    direction_button.pack()

    # Lesson checkboxes
    tk.Label(root, text="Lektion(en) auswählen:").pack()
    check_frame = tk.Frame(root)
    check_frame.pack()
    check_vars = {}
    for file in load_lecture_files():
        var = tk.BooleanVar()
        cb = tk.Checkbutton(check_frame, text=file, variable=var, command=update_selected_lessons)
        cb.pack(anchor="w")
        check_vars[file] = var

    word_label = tk.Label(root, text="", font=("Helvetica", 20))
    word_label.pack(pady=20)

    entry = tk.Entry(root, font=("Helvetica", 16))
    entry.pack(pady=10)
    entry.bind("<Return>", check_answer)
    entry.bind("<Right>", next_word)
    entry.bind("<Left>", previous_word)

    feedback_label = tk.Label(root, text="", font=("Helvetica", 14))
    feedback_label.pack(pady=10)

    tk.Button(root, text="Weiter", command=next_word).pack(pady=5)
    tk.Button(root, text="Statistik anzeigen", command=show_stats).pack(pady=5)
    tk.Button(root, text="Zurück zum Hauptmenü", command=lambda: (root.destroy(), __import__('app').main_menu())).pack(pady=20)

    root.mainloop()
