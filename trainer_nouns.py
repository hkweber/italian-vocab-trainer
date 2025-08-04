import tkinter as tk
import tkinter.messagebox as messagebox
import random, os, json, time


# ── SRS helper ────────────────────────────────────────────
class SRS:
    def __init__(self, filename="srs_nouns.json"):
        self.progress_file = filename
        self.progress = self.load_progress()

    def normalize_key(self, text: str) -> str:
        # unify quotes, lowercase, trim
        return text.lower().replace("’", "'").strip()

    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_progress(self):
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f)

    def get_due_words(self, words):
        words = [self.normalize_key(w) for w in words]
        now = time.time()
        return [
            w for w in words
            if self.progress.get(w, {"due": 0})["due"] <= now
        ]

    def update(self, word, correct: bool):
        word = self.normalize_key(word)
        now = time.time()
        rec = self.progress.get(word, {"interval": 1, "due": now, "ease": 2.5})
        if correct:
            rec["interval"] = max(1, int(rec["interval"] * rec["ease"]))
            rec["ease"] = min(3.0, rec["ease"] + 0.1)
        else:
            rec["interval"] = 1
            rec["ease"] = max(1.3, rec["ease"] - 0.2)
        rec["due"] = now + rec["interval"] * 86_400   # 1 day
        self.progress[word] = rec
        self.save_progress()


# ── utility functions ─────────────────────────────────────
def load_lecture_files():
    path = os.path.join("lectures", "nouns")
    return [f for f in os.listdir(path) if f.endswith(".json")]


def load_lecture(files):
    data = {}
    for name in files:
        fp = os.path.join("lectures", "nouns", name)
        with open(fp, "r", encoding="utf-8") as f:
            part = json.load(f)
        for k, v in part.items():
            if isinstance(v, dict) and "de" in v:
                data[k] = v
    return data


def norm(text: str) -> str:
    return text.lower().replace("’", "'").strip()


def strip_article(de_word: str) -> str:
    de_word = norm(de_word)
    for art in ("der ", "die ", "das "):
        if de_word.startswith(art):
            return de_word[len(art):]
    return de_word


# ── main UI ───────────────────────────────────────────────
def start_noun_trainer(previous_window):
    previous_window.destroy()
    root = tk.Tk()
    root.title("Vokabeltrainer – Substantive")

    srs = SRS()
    selected_files = []
    nouns = {}
    reverse = False
    current_word, history, idx = None, [], -1
    stats = {"correct": 0, "wrong": 0}

    # ----- helpers -----
    def toggle_direction():
        nonlocal reverse
        reverse = not reverse
        dir_btn.config(text=f"Richtung: {'IT→DE' if not reverse else 'DE→IT'}")
        next_word()

    def refresh_selection():
        nonlocal selected_files, nouns, history, idx
        selected_files = [f for f, var in chk_vars.items() if var.get()]
        if not selected_files:
            fb_lbl.config(text="⚠️ keine Lektion gewählt", fg="orange")
            return
        nouns = load_lecture(selected_files)
        history, idx = [], -1
        next_word()

    def next_word(_=None):
        nonlocal current_word, idx
        if not nouns:
            fb_lbl.config(text="⚠️ nichts geladen", fg="orange")
            return
        entry.delete(0, tk.END)
        fb_lbl.config(text="")
        pool = srs.get_due_words(list(nouns.keys())) or list(nouns.keys())
        current_word = random.choice(pool)
        history.append(current_word)
        idx = len(history) - 1
        q_lbl.config(text=current_word if not reverse else nouns[current_word]["de"])

    def prev_word(_=None):
        nonlocal current_word, idx
        if idx > 0:
            idx -= 1
            current_word = history[idx]
            q_lbl.config(text=current_word if not reverse else nouns[current_word]["de"])
            entry.delete(0, tk.END)
            fb_lbl.config(text="")

    def check(_=None):
        answer = norm(entry.get())

        if not reverse:          # IT → DE
            corr_field = nouns[current_word]["de"]
            corr_list = corr_field if isinstance(corr_field, list) else [corr_field]
            corr_clean = [strip_article(norm(c)) for c in corr_list]
            ok = strip_article(answer) in corr_clean
        else:                    # DE → IT
            ok = answer == norm(current_word)

                # pick the right string to show as the correct answer
        if reverse:                       # DE → IT   → show Italian
            correct_display = current_word
        else:                             # IT → DE   → show German(s)
            corr_field = nouns[current_word]["de"]
            correct_display = ", ".join(corr_field) if isinstance(corr_field, list) else corr_field

        fb_lbl.config(
            text="✅ Richtig!" if ok else f"❌ Falsch. Korrekt: {correct_display}",
            fg="green" if ok else "red"
        )
        stats["correct" if ok else "wrong"] += 1
        srs.update(current_word, ok)

    def show_stats():
        total = stats["correct"] + stats["wrong"]
        msg = (f"Beantwortet: {total}\n"
               f"✅ Richtig : {stats['correct']}\n"
               f"❌ Falsch  : {stats['wrong']}")
        messagebox.showinfo("Statistik", msg)

    # ----- UI -----
    tk.Label(root, text="Substantiv-Übung", font=("Helvetica", 16)).pack(pady=8)
    dir_btn = tk.Button(root, text="Richtung: IT→DE", command=toggle_direction); dir_btn.pack()

    tk.Label(root, text="Lektionen wählen:").pack()
    frm = tk.Frame(root); frm.pack()
    chk_vars = {}
    for f in load_lecture_files():
        var = tk.BooleanVar()
        tk.Checkbutton(frm, text=f, variable=var, command=refresh_selection).pack(anchor="w")
        chk_vars[f] = var

    q_lbl = tk.Label(root, text="", font=("Helvetica", 20)); q_lbl.pack(pady=16)

    entry = tk.Entry(root, font=("Helvetica", 16)); entry.pack(pady=4)
    entry.bind("<Return>", check)
    entry.bind("<Up>", next_word)
    entry.bind("<Down>", prev_word)

    fb_lbl = tk.Label(root, text="", font=("Helvetica", 14)); fb_lbl.pack(pady=6)

    tk.Button(root, text="Weiter", command=next_word).pack(pady=4)
    tk.Button(root, text="Statistik", command=show_stats).pack(pady=4)
    tk.Button(root, text="Zurück", command=lambda: (root.destroy(), __import__('app').main_menu())).pack(pady=10)

    root.mainloop()
