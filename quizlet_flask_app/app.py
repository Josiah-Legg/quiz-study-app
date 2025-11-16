import os
import random
import json
import base64
from flask import Flask, render_template, request, redirect, url_for

def load_vocab(filename):
    vocab = {}
    with open(filename, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        if len(lines) % 2 != 0:
            raise ValueError("terms.txt must have pairs of lines (latin then english).")
        for i in range(0, len(lines), 2):
            latin = lines[i]
            english = lines[i + 1]
            vocab[latin] = [eng.strip() for eng in english.split(",")]
    return vocab

def encode_state(state: dict) -> str:
    """JSON -> base64 string safe to put in a hidden input value."""
    return base64.b64encode(json.dumps(state).encode("utf-8")).decode("ascii")

def decode_state(s: str) -> dict:
    """base64 string -> JSON dict."""
    return json.loads(base64.b64decode(s.encode("ascii")).decode("utf-8"))

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOCAB = load_vocab(os.path.join(BASE_DIR, "terms.txt"))


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/quiz", methods=["POST", "GET"])
def quiz():
    if request.method == "GET":
        remaining = list(VOCAB.keys())
        random.shuffle(remaining)
        total_terms = len(remaining)
        current = random.choice(remaining) if remaining else None
        state = {
            "remaining": remaining,
            "total_terms": total_terms,
            "total_questions": 0,
            "correct_answers": 0,
            "current": current,
        }
        return render_template(
            "quiz.html",
            current=current,
            state_b64=encode_state(state),
            progress_done=0,
            total_terms=total_terms,
            remaining_count=len(remaining),
            total_questions=0,
            correct_answers=0,
            feedback=None,
        )

    form = request.form
    state_b64 = form.get("state")
    if not state_b64:
        return redirect(url_for("index"))

    try:
        state = decode_state(state_b64)
    except Exception:
        return redirect(url_for("index"))

    remaining = state.get("remaining", [])
    total_terms = state.get("total_terms", len(remaining))
    total_questions = int(state.get("total_questions", 0))
    correct_answers = int(state.get("correct_answers", 0))
    current = state.get("current")

    if form.get("__advance") == "1":
        if not remaining:
            return redirect(url_for("complete", total_questions=total_questions, correct_answers=correct_answers))
        current = random.choice(remaining)
        state["current"] = current
        return render_template(
            "quiz.html",
            current=current,
            state_b64=encode_state(state),
            progress_done=total_terms - len(remaining),
            total_terms=total_terms,
            remaining_count=len(remaining),
            total_questions=total_questions,
            correct_answers=correct_answers,
            feedback=None,
        )

    answer_raw = form.get("answer", "")
    answer = answer_raw.strip().lower()
    total_questions += 1

    valid_answers_raw = VOCAB.get(current, [])
    if isinstance(valid_answers_raw, str):
        valid_answers_raw = [x.strip() for x in valid_answers_raw.split(",")]
    valid_answers = [v.lower() for v in valid_answers_raw]

    if answer and answer in valid_answers:
        correct_answers += 1
        if current in remaining:
            remaining.remove(current)
        feedback = ["Correct!", True]
    else:
        feedback = [f"Incorrect, the correct answers are: {', '.join(valid_answers_raw)}", False]

    state = {
        "remaining": remaining,
        "total_terms": total_terms,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "current": current,
    }

    return render_template(
        "quiz.html",
        current=current,
        state_b64=encode_state(state),
        progress_done=total_terms - len(remaining),
        total_terms=total_terms,
        remaining_count=len(remaining),
        total_questions=total_questions,
        correct_answers=correct_answers,
        feedback=feedback,
    )


@app.route("/complete")
def complete():
    try:
        total_questions = int(request.args.get("total_questions", 0))
        correct_answers = int(request.args.get("correct_answers", 0))
    except ValueError:
        return redirect(url_for("index"))
    pct = (correct_answers / total_questions * 100) if total_questions else 0.0
    return render_template("complete.html", total_questions=total_questions, correct_answers=correct_answers, percentage=pct)


if __name__ == "__main__":
    app.run(debug=True)
