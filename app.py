from flask import Flask, jsonify, request
import csv
import random
from collections import Counter

app = Flask(__name__)

HISTORY_FILE = "539_history.csv"
history = []

def load_history():
    global history
    with open(HISTORY_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        history = [list(map(int, row[2:7])) for row in reader]

load_history()

def analyze(mode="stable"):

    counter = Counter()
    last_seen = {n: None for n in range(1, 40)}
    total_draws = len(history)

    for idx, draw in enumerate(history):
        for num in draw:
            counter[num] += 1
            last_seen[num] = idx

    # 最近50期加權
    for draw in history[-50:]:
        for num in draw:
            counter[num] += 2

    # 遺漏值加權
    for n in range(1, 40):
        if last_seen[n] is not None:
            miss = total_draws - last_seen[n]
            counter[n] += miss * 0.2

    numbers = list(range(1, 40))

    if mode == "aggressive":
        weights = [counter[n] ** 1.5 for n in numbers]
    elif mode == "cold":
        weights = [(max(counter.values()) - counter[n] + 1) for n in numbers]
    else:  # stable
        weights = [counter[n] for n in numbers]

    selected = random.choices(numbers, weights=weights, k=5)

    total_weight = sum(weights)
    probabilities = {
        n: round((counter[n] / total_weight) * 100, 2)
        for n in numbers
    }

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    return sorted(list(set(selected)))[:5], hot, cold, probabilities


@app.route("/generate")
def generate():
    mode = request.args.get("mode", "stable")
    nums, hot, cold, prob = analyze(mode)
    return jsonify({
        "numbers": nums,
        "hot": hot,
        "cold": cold,
        "probabilities": prob
    })


@app.route("/history")
def history_query():
    period = request.args.get("period")
    for row in history:
        pass
    return jsonify({"message": "history endpoint ready"})


@app.route("/")
def home():
    return "539 Cloud AI Advanced Running"

if __name__ == "__main__":
    app.run()
