import tkinter as tk
import tkinter.messagebox as messagebox
import random, os, json, time, re


# ── SRS helper ───────────────────────────────────────────
class SRS:
    def __init__(self, filename="srs_nouns.json"):
        self.progress_file = filename
        self.progress = self.load_progress()

    def normalize_key(self, txt: str) -> str:
        return txt.lower().replace("’", "'").strip()

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
        return [w for w in words if self.progress.get(w, {"due": 0})["due"] <= now]

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
        rec["due"] = now + rec["interval"] * 86_400
        self.progress[word] = rec
        self.save_progress()


# ── article / plural helpers ─────────────────────────────
def norm(txt: str) -> str:
    return txt.lower().replace("’", "'").strip()


def strip_article(de_word: str) -> str:
    de_word = norm(de_word)
    for art in ("der ", "die ", "das "):
        if de_word.startswith(art):
            return de_word[len(art):]
    return de_word


def _gender_from_article(article: str, noun_root: str) -> str:
    if article in ("il", "lo"):
        return "m"
    if article == "la":
        return "f"
    if article == "l'":
        return "f" if noun_root.endswith("a") else "m"
    return "m"


def italian_plural(word_with_article: str) -> str:
    word_with_article = norm(word_with_article)
    m = re.match(r"(il|lo|la|l')\s*('?)(.+)", word_with_article)
    if not m:
        return word_with_article
    art, _, root = m.groups()
    gender = _gender_from_article(art, root)

    if gender == "f":
        pl_art = "le"
    else:
        pl_art = "gli" if art in ("lo", "l'") else "i"

    if   root.endswith("o"): root_pl = root[:-1] + "i"
    elif root.endswith("a"): root_pl = root[:-1] + "e"
    elif root.endswith("e"): root_pl = root[:-1] + "i"
    else:                    root_pl = root

    return f"{pl_art} {root_pl}"


def indef_article(word_with_article: str) -> str:
    word_with_article = norm(word_with_article)
    m = re.match(r"(il|lo|la|l')\s*('?)(.+)", word_with_article)
    if not m:
        return "un"
    art, _, root = m.groups()
    gender = _gender_from_article(art, root)

    if gender == "f":
        return "un’" if root[0] in "aeiou" else "una"
    if art == "lo" or root[:2] in ("ps", "gn") or re.match(r"[sxz][a-z]", root):
        return "uno"
    return "un"


# ── file helpers ─────────────────────────────────────────
def lecture_files():
    p = os.path.join("lectures", "nouns")
    return [f for f in os.listdir(p) if f.endswith(".json")]


def load_lecture(file_list):
    data = {}
    for name in file_list:
        with open(os.path.join("lectures", "nouns", name), encoding="utf-8") as f:
            part = json.load(f)
        for k, v in part.items():
            if isinstance(v, dict) and "de" in v:
                k_norm = k.replace("’", "'").strip()
                data[k_norm] = v
    return data


# ── main GUI ─────────────────────────────────────────────
def start_noun_trainer(prev):
    prev.destroy()
    root = tk.Tk()
    root.title("Vokabeltrainer – Substantive")

    reverse = False
    
    # pick the right SRS file for the current direction
    def make_srs():
        filename = "srs_nouns_de2it.json" if reverse else "srs_nouns_it2de.json"
        return SRS(filename)

    srs = make_srs()

    selected, nouns = [], {}
    reverse = False
    current, history, idx = None, [], -1
    stats = {"correct": 0, "wrong": 0}

    # ----- inner helpers --------------------------------
    def toggle_dir():
        nonlocal reverse, srs
        reverse = not reverse
        srs = make_srs()                     # load the other SRS file
        dir_btn.config(text=f"Richtung: {'IT→DE' if not reverse else 'DE→IT'}")
        next_word()

    def refresh_sel():
        nonlocal selected, nouns, history, idx
        selected = [f for f, v in chk_vars.items() if v.get()]
        if not selected:
            fb_lbl.config(text="⚠️ none selected", fg="orange")
            return
        nouns = load_lecture(selected)
        history, idx = [], -1
        next_word()

    def next_word(_=None):
        nonlocal current, idx
        if not nouns:
            return
        entry.delete(0, tk.END)
        fb_lbl.config(text="")

        pool = srs.get_due_words(list(nouns.keys())) or list(nouns.keys())
        current = random.choice(pool)
        history.append(current)
        idx = len(history) - 1

        mode = current_mode.get()
        if mode == "Translate":
            prompt = current if not reverse else nouns[current]["de"]
            if isinstance(prompt, list):
                prompt = prompt[0]
        else:          # Plural or Indef. article → always show singular IT
            prompt = current

        q_lbl.config(text=prompt)

    def prev_word(_=None):
        nonlocal current, idx
        if idx > 0:
            idx -= 1
            current = history[idx]
            q_lbl.config(text=current)
            entry.delete(0, tk.END)
            fb_lbl.config(text="")

    def check(_=None):
        answer = norm(entry.get())
        mode = current_mode.get()

        if mode == "Translate":
            if not reverse:
                corr = nouns[current]["de"]
                corr_list = corr if isinstance(corr, list) else [corr]
                ok = strip_article(answer) in [strip_article(norm(c)) for c in corr_list]
                correct_disp = ", ".join(corr_list) if isinstance(corr, list) else corr
            else:
                ok = answer == norm(current)
                correct_disp = current

        elif mode == "Plural form":
            correct_disp = italian_plural(current)
            ok = answer == norm(correct_disp)

        elif mode == "Indef. article":
            correct_disp = indef_article(current)          # una / un / uno / un’
            # ---- also allow "una difficoltà" etc. ----
            # get the noun without its definite article
            noun_root = re.sub(r"^(il|lo|la|l')\s*'?","", norm(current))
            ok = (
                answer == norm(correct_disp) or
                answer == norm(f"{correct_disp} {noun_root}")
            )


        fb_lbl.config(
            text="✅ Correct!" if ok else f"❌ Wrong. {correct_disp}",
            fg="green" if ok else "red"
        )
        stats["correct" if ok else "wrong"] += 1
        srs.update(current, ok)

    def show_stats():
        tot = stats["correct"] + stats["wrong"]
        messagebox.showinfo(
            "Stats",
            f"Answered: {tot}\n✅ {stats['correct']}\n❌ {stats['wrong']}"
        )

    # ----- UI layout ------------------------------------
    tk.Label(root, text="Substantive trainer", font=("Helvetica", 16)).pack(pady=6)

    dir_btn = tk.Button(root, text="Richtung: IT→DE", command=toggle_dir)
    dir_btn.pack()

    tk.Label(root, text="Choose lessons:").pack()
    frm = tk.Frame(root)
    frm.pack()
    chk_vars = {}
    for f in lecture_files():
        var = tk.BooleanVar()
        chk_vars[f] = var
        tk.Checkbutton(frm, text=f, variable=var, command=refresh_sel).pack(anchor="w")

    # Exercise modes
    modes = ("Translate", "Plural form", "Indef. article")
    current_mode = tk.StringVar(value=modes[0])
    tk.Label(root, text="Exercise mode:").pack(pady=(4, 0))
    tk.OptionMenu(root, current_mode, *modes).pack()

    q_lbl = tk.Label(root, text="", font=("Helvetica", 20))
    q_lbl.pack(pady=14)

    entry = tk.Entry(root, font=("Helvetica", 16))
    entry.pack(pady=4)
    entry.bind("<Return>", check)
    entry.bind("<Up>", next_word)     # next
    entry.bind("<Down>", prev_word)   # previous

    fb_lbl = tk.Label(root, text="", font=("Helvetica", 14))
    fb_lbl.pack(pady=6)

    tk.Button(root, text="Next", command=next_word).pack(pady=3)
    tk.Button(root, text="Stats", command=show_stats).pack(pady=3)
    tk.Button(root, text="Back", command=lambda: (root.destroy(), __import__('app').main_menu())).pack(pady=10)

    root.mainloop()
