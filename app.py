from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
from collections import Counter
import random

app = Flask(__name__)

history = []

URL = "https://www.taiwanlottery.com/lotto/result/daily_cash"

def fetch_latest():
    global history
    try:
        r = requests.get(URL, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        rows = soup.select("table tbody tr")

        history.clear()

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue

            period = cols[0].text.strip()
            date = cols[1].text.strip()

            numbers = [
                int(cols[2].text.strip()),
                int(cols[3].text.strip()),
                int(cols[4].text.strip()),
                int(cols[5].text.strip()),
                int(cols[6].text.strip())
            ]

            history.append({
                "period": period,
                "date": date,
                "numbers": numbers
            })

        print("抓取成功:", len(history))

    except Exception as e:
        print("抓取失敗:", e)


def build_weights():
    counter = Counter()
    for row in history:
        for n in row["numbers"]:
            counter[n] += 1
    return counter


@app.route("/generate")
def generate():

    if not history:
        fetch_latest()

    if not history:
        draw = sorted(random.sample(range(1, 40), 5))
        return jsonify({
            "numbers": draw,
            "hot": [],
            "cold": [],
            "mode": "fallback_random"
        })

    counter = build_weights()
    numbers = list(range(1, 40))
    weights = [counter[n] if counter[n] > 0 else 1 for n in numbers]

    draw = sorted(random.choices(numbers, weights=weights, k=5))

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    return jsonify({
        "numbers": draw,
        "hot": hot,
        "cold": cold,
        "mode": "weighted"
    })


@app.route("/history")
def history_query():

    if not history:
        fetch_latest()

    period = request.args.get("period")

    for row in history:
        if row["period"] == period:
            return jsonify(row)

    return jsonify({"error": "period not found"}), 404


@app.route("/")
def home():
    return "539來財 穩定抓官網版運行中"


if __name__ == "__main__":
    app.run()
