from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template

app = FastAPI()

# Store player names and scores
players = []
scores = {}

template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 0;
            padding: 10px;
            max-width: 390px;
            margin: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid black;
            padding: 10px;
            text-align: center;
        }
        input {
            width: 90%;
            font-size: 16px;
            padding: 5px;
        }
        button {
            font-size: 16px;
            padding: 10px;
            width: 100%;
        }
    </style>
    <script>
        async function addPlayer() {
            let playerInput = document.getElementById("player").value;
            let playerList = playerInput.split(',').map(name => name.trim()).filter(name => name.length > 0);
            for (let player of playerList) {
                await fetch("/add_player", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ "player": player })
                });
            }
            await updateTable();
            closePlayerPopup();
        }

        function makeCellEditable(cell, player, round) {
            let oldValue = cell.innerText;
            let input = document.createElement("input");
            input.type = "text";
            input.inputMode = "numeric";
            input.pattern = "[0-9]*";
            input.value = oldValue;
            input.style.width = "50px"; 
            input.onblur = async function() {
                let newScore = parseInt(input.value);
                if (!isNaN(newScore) && newScore >= 0) {
                    await fetch("/add_score", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ "player": player, "score": newScore, "round": round })
                    });
                    await updateTable();
                } else {
                    cell.innerText = oldValue;
                }
            };
            input.onkeypress = function(event) {
                if (event.key === "Enter") {
                    input.blur();
                }
            };
            cell.innerText = "";
            cell.appendChild(input);
            input.focus();
        }

        async function updateTable() {
            let response = await fetch("/");
            let text = await response.text();
            document.documentElement.innerHTML = text;
        }

        function openPlayerPopup() {
            let popup = document.getElementById("playerPopup");
            popup.style.display = "flex";
        }

        function closePlayerPopup() {
            document.getElementById("playerPopup").style.display = "none";
            document.getElementById("player").value = "";
        }

        function resetGame() {
            fetch('/reset').then(() => location.reload());
        }
    </script>
</head>
<body onload="openPlayerPopup()">
    <div id="playerPopup" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: none; align-items: center; justify-content: center;">
        <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h3>Add Player Names as Comma Separated List</h3>
            <input type="text" id="player" placeholder="Enter player names (comma-separated)">
            <button onclick="addPlayer()">Start Game</button>
        </div>
    </div>
    <table border="1">
        <tr>
            <th>Round</th>
            {% for player in players %}
                <th>{{ player }}</th>
            {% endfor %}
        </tr>
        {% for round in range(max_rounds + 1) %}
        <tr>
            <td>{{ round + 1 }}</td>
            {% for player in players %}
                <td onclick="makeCellEditable(this, '{{ player }}', {{ round }})">
                    {% set player_scores = scores.get(player, []) %}
                    {{ player_scores[round] if round < player_scores|length else '' }}
                </td>
            {% endfor %}
        </tr>
        {% endfor %}
        <tr>
            <td><strong>Total</strong></td>
            {% for player in players %}
                <td><strong>{{ "{:,}".format(scores.get(player, [])|sum) }}</strong></td>
            {% endfor %}
        </tr>
    </table>
    <button onclick="resetGame()" style="margin-top: 20px; padding: 10px; font-size: 16px;">Reset Game</button>
</body>
</html>
""")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    max_rounds = max([len(s) for s in scores.values()] + [10])
    return template.render(players=players, scores=scores, max_rounds=max_rounds)

@app.post("/add_player")
async def add_player(data: dict):
    if data["player"] not in players:
        players.append(data["player"])
        scores[data["player"]] = []
    return {"message": "Player added"}

@app.post("/add_score")
async def add_score(data: dict):
    if data["player"] in players:
        round_index = data.get("round", len(scores[data["player"]]))
        while len(scores[data["player"]]) <= round_index:
            scores[data["player"]].append(0)
        scores[data["player"]][round_index] = data["score"]
    return {"message": "Score added"}

@app.get("/reset")
async def reset_game():
    players.clear()
    scores.clear()
    return RedirectResponse(url="/")
