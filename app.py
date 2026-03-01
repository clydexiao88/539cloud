from flask import Flask, jsonify, request
import csv
from collections import Counter
import random

app = Flask(__name__)

HISTORY_FILE = "539_history.csv"
history = []


# ===============================
# 載入歷史資料
# ===============================
def load_history():
    global history
    history.clear()

    with open(HISTORY_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            history.append({
                "period": row[0],
                "date": row[1],
                "numbers": list(map(int, row[2:7]))
            })

    print("載入完成:", len(history))


load_history()


# ===============================
# 計算權重
# ===============================
def build_weights(last_n=None):

    data = history[-last_n:] if last_n else history

    counter = Counter()

    for row in data:
        for n in row["numbers"]:
            counter[n] += 1

    return counter


# ===============================
# AI 產生選號
# ===============================
@app.route("/generate")
def generate():

    mode = request.args.get("mode", "balanced")

    if not history:
        return jsonify({"error": "沒有歷史資料"}), 500

    counter = build_weights()

    numbers = list(range(1, 40))

    if mode == "aggressive":
        weights = [counter[n] ** 1.5 for n in numbers]

    elif mode == "cold":
        max_val = max(counter.values())
        weights = [(max_val - counter[n] + 1) for n in numbers]

    else:  # balanced
        weights = [counter[n] if counter[n] > 0 else 1 for n in numbers]

    selected = sorted(random.choices(numbers, weights=weights, k=5))

    total = sum(counter.values())

    probabilities = {
        n: round((counter[n] / total) * 100, 2)
        for n in numbers
    }

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    # 近50期統計
    recent_counter = build_weights(last_n=50)

    return jsonify({
        "mode": mode,
        "numbers": selected,
        "hot": hot,
        "cold": cold,
        "probabilities": probabilities,
        "recent_trend": dict(recent_counter)
    })


# ===============================
# 歷史查詢
# ===============================
@app.route("/history")
def history_query():

    period = request.args.get("period")

    for row in history:
        if row["period"] == period:
            return jsonify(row)

    return jsonify({"error": "查無此期數"}), 404


@app.route("/reload")
def reload_data():
    load_history()
    return jsonify({
        "status": "reloaded",
        "records": len(history)
    })


@app.route("/")
def home():
    return "539來財 Pro 分析版運行中"


if __name__ == "__main__":
    app.run()
