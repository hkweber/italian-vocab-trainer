import tkinter as tk
import random
import os
import json

def load_lecture_files():
    path = os.path.join("lectures", "nouns")
    files = [f for f in os.listdir(path) if f.endswith(".json")]
    return files

def load_noun_lecture(filename):
    path = os.path.join("lectures", "nouns", filename)
    with open(path, "r", encoding="utf-8") as f:
        content = json.load(f)
        return {
            key: value for key, value in content.items()
            if isinstance(value, dict) and "de" in value
        }

def normalize(text):
    return text.lower().replace("’", "'").strip()

def strip_german_article(text):
    text = normalize(text)
    for article in ["der ", "die ", "das "]:
        if text.startswith(article):
            return text[len(article):]
    return text

def start_noun_trainer(previous_window):
    previous_window.destroy()
    root = tk.Tk()
    root.title("Vokabeltrainer – Substantive")

    lecture_files = load_lecture_files()
    current_lecture = tk.StringVar()
    current_lecture.set(lecture_files[0])

    nouns = load_noun_lecture(current_lecture.get())
    reverse = False
    current_word = None
    word_history = []
    history_index = -1

    def toggle_direction():
        nonlocal reverse
        reverse = not reverse
        direction_button.config(text=f"Richtung: {'Italienisch → Deutsch' if not reverse else 'Deutsch → Italienisch'}")
        next_word()

    def choose_lecture(name):
        nonlocal nouns, word_history, history_index
        nouns = load_noun_lecture(name)
        word_history = []
        history_index = -1
        next_word()

    def next_word(event=None):
        nonlocal current_word, history_index
        entry.delete(0, tk.END)
        feedback_label.config(text="")
        current_word = random.choice(list(nouns.keys()))
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
        user = normalize(entry.get())
        if not reverse:
            correct = normalize(nouns[current_word]["de"])
            user_clean = strip_german_article(user)
            correct_clean = strip_german_article(correct)
        else:
            correct = normalize(current_word)
            user_clean = user
            correct_clean = correct

        if user_clean == correct_clean:
            feedback_label.config(text="✅ Richtig!", fg="green")
        else:
            feedback_label.config(text=f"❌ Falsch. Korrekt: {correct}", fg="red")

    # UI
    tk.Label(root, text="Substantiv-Übung", font=("Helvetica", 16)).pack(pady=10)

    direction_button = tk.Button(root, text="Richtung: Italienisch → Deutsch", command=toggle_direction)
    direction_button.pack()

    tk.Label(root, text="Lektion auswählen:").pack()
    lecture_menu = tk.OptionMenu(root, current_lecture, *lecture_files, command=choose_lecture)
    lecture_menu.pack(pady=5)

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
    tk.Button(root, text="Zurück zum Hauptmenü", command=lambda: (root.destroy(), __import__('app').main_menu())).pack(pady=20)

    next_word()
    root.mainloop()
