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

def build_weights():

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

    # 遺漏值
    for n in range(1, 40):
        if last_seen[n] is not None:
            miss = total_draws - last_seen[n]
            counter[n] += miss * 0.2

    return counter

def monte_carlo(counter, mode="stable"):

    numbers = list(range(1, 40))

    if mode == "aggressive":
        weights = [counter[n] ** 1.5 for n in numbers]
    elif mode == "cold":
        weights = [(max(counter.values()) - counter[n] + 1) for n in numbers]
    else:
        weights = [counter[n] for n in numbers]

    simulation_counter = Counter()

    # 🔥 200次模擬（安全值）
    for _ in range(200):
        draw = random.choices(numbers, weights=weights, k=5)
        for n in draw:
            simulation_counter[n] += 1

    best = [n for n, _ in simulation_counter.most_common(5)]

    return sorted(best)

@app.route("/generate")
def generate():

    mode = request.args.get("mode", "stable")

    counter = build_weights()

    selected = monte_carlo(counter, mode)

    total_weight = sum(counter.values())
    probabilities = {
        n: round((counter[n] / total_weight) * 100, 2)
        for n in range(1, 40)
    }

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    return jsonify({
        "numbers": selected,
        "hot": hot,
        "cold": cold,
        "probabilities": probabilities
    })

@app.route("/")
def home():
    return "539 Cloud AI Monte Carlo Running"

if __name__ == "__main__":
    app.run()
