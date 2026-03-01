from flask import Flask, jsonify, request
import requests
from collections import Counter
import random

app = Flask(__name__)

history = []

TAIWAN_API = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Daily539Result"


# ===============================
# 抓最新開獎資料
# ===============================
def fetch_latest():
    global history
    try:
        url = f"{TAIWAN_API}?period&startMonth=2025-01&endMonth=2026-12"
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            print("API status error:", r.status_code)
            return

        data = r.json()

        if "content" not in data:
            print("API format error")
            return

        result_list = data["content"].get("daily539Res", [])

        if not result_list:
            print("No data returned")
            return

        history.clear()

        for item in result_list:
            history.append({
                "period": str(item["period"]),
                "date": item["lotteryDate"][:10],
                "numbers": item["drawNumberAppear"]
            })

        print("History updated:", len(history))

    except Exception as e:
        print("Update failed:", e)


# ===============================
# 計算熱度
# ===============================
def build_weights():
    counter = Counter()
    for row in history:
        for n in row["numbers"]:
            counter[n] += 1
    return counter


# ===============================
# 產生 AI 選號
# ===============================
@app.route("/generate")
def generate():

    if not history:
        fetch_latest()

    # 若抓不到資料 → fallback 隨機
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

    # 保證權重至少為 1
    weights = [counter[n] if counter[n] > 0 else 1 for n in numbers]

    draw = random.choices(numbers, weights=weights, k=5)
    draw = sorted(draw)

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    return jsonify({
        "numbers": draw,
        "hot": hot,
        "cold": cold,
        "mode": "weighted"
    })


# ===============================
# 歷史查詢
# ===============================
@app.route("/history")
def history_query():

    if not history:
        fetch_latest()

    period = request.args.get("period")

    if not period:
        return jsonify({"error": "please provide period"}), 400

    for row in history:
        if row["period"] == period:
            return jsonify(row)

    return jsonify({"error": "period not found"}), 404


# ===============================
# 手動強制更新
# ===============================
@app.route("/update")
def update():
    fetch_latest()
    return jsonify({
        "status": "updated",
        "records": len(history)
    })


# ===============================
# 首頁
# ===============================
@app.route("/")
def home():
    return "539來財 正式商用穩定版運行中"


if __name__ == "__main__":
    app.run()
