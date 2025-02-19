from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from jinja2 import Template

app = FastAPI()

# Global variables to store player names and their respective scores.
players = []
scores = {}  # Dictionary mapping player names to their score lists.

template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <style>
        /* Base styling with a calming blue gradient background */
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 0;
            padding: 10px;
            max-width: 390px;
            margin: auto;
            background: linear-gradient(to bottom, #e0f7fa, #80deea);
            color: #333;
        }
        /* Table styling with subtle shadows and a deep blue header */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background-color: #fff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            table-layout: fixed;
        }
        /* Styling for all table headers and cells */
        th, td {
            padding: 10px;
            text-align: center;
            word-wrap: break-word;
        }
        /* Fix the leftmost column (round numbers) to a minimal width */
        table th:first-child,
        table td:first-child {
            width: 40px;    /* Fixed minimal width */
            padding: 5px;   /* Reduced padding for a compact look */
        }
        th {
            background-color: #1e3a5f; /* Deep blue header */
            color: #fff;
        }
        td {
            border: 1px solid #ddd;
        }
        /* Input styling */
        input {
            width: 90%;
            font-size: 16px;
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        /* Button styling with green accents and a hover effect */
        button, .button-link {
            background-color: #5DAE8B; /* Green accent */
            border: none;
            color: #fff;
            font-size: 16px;
            padding: 10px;
            cursor: pointer;
            border-radius: 5px;
            text-decoration: none;
            text-align: center;
        }
        button:hover, .button-link:hover {
            background-color: #3e8e60;
        }
        /* Container to hold the reset button and game rules link side by side */
        .button-container {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-top: 10px;
        }
        .button-container button,
        .button-container a {
            width: 48%;
        }
        /* Popup overlay and inner box styling */
        #playerPopup {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: none;
            align-items: center;
            justify-content: center;
        }
        #playerPopup > div {
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        /* Styling for the scoring image to scale to the container's width */
        .scoring-image {
            width: 100%;
            max-width: 100%;
            display: block;
            margin-top: 20px;
            border: 1px solid #ddd;
        }
    </style>
    <script>
        // Function to add one or more players based on comma-separated input.
        async function addPlayer() {
            let playerInput = document.getElementById("player").value;
            // Split input by commas, trim whitespace, and filter out empty strings.
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

        // Makes a table cell editable so that the score can be updated.
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

        // Reloads the table content by fetching the updated HTML from the server.
        async function updateTable() {
            let response = await fetch("/");
            let text = await response.text();
            document.documentElement.innerHTML = text;
        }

        // Opens the popup to add players.
        function openPlayerPopup() {
            let popup = document.getElementById("playerPopup");
            popup.style.display = "flex";
        }

        // Closes the player input popup and clears the input field.
        function closePlayerPopup() {
            document.getElementById("playerPopup").style.display = "none";
            document.getElementById("player").value = "";
        }

        // Function to reset the game.
        function resetGame() {
            // Show a confirmation dialog to the user.
            if (confirm("Are you sure you want to reset the game? This will clear all players and scores.")) {
                fetch('/reset').then(() => location.reload());
            }
        }
    </script>
</head>
<body onload="openPlayerPopup()">
    <!-- Popup for entering player names -->
    <div id="playerPopup">
        <div>
            <h3>Add Player Names as Comma Separated List</h3>
            <input type="text" id="player" placeholder="Enter player names (ex. Meg, JH, James)">
            <button onclick="addPlayer()">Start Game</button>
        </div>
    </div>
    <!-- Scoreboard table -->
    <table border="1">
        <tr>
            <!-- Minimal round indicator column header: intentionally left blank -->
            <th></th>
            {% for player in players %}
                <th>{{ player }}</th>
            {% endfor %}
        </tr>
        {% for round in range(max_rounds + 1) %}
        <tr>
            <!-- The round number is still displayed in the leftmost column -->
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
    <!-- Container for Reset Game and Game Rules controls -->
    <div class="button-container">
        <button onclick="resetGame()">Reset Game</button>
        <a class="button-link" href="/rules.pdf" target="_blank">Game Rules</a>
    </div>
    <!-- Scoring image added below all other content -->
    <img class="scoring-image" src="/scoring.jpeg" alt="Scoring Image">
</body>
</html>
""")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Determine the number of rounds to display based on the longest score list (or default to 10)
    max_rounds = max([len(s) for s in scores.values()] + [10])
    return template.render(players=players, scores=scores, max_rounds=max_rounds)

@app.post("/add_player")
async def add_player(data: dict):
    # Add a new player if they are not already in the list.
    if data["player"] not in players:
        players.append(data["player"])
        scores[data["player"]] = []  # Initialize the player's score list.
    return {"message": "Player added"}

@app.post("/add_score")
async def add_score(data: dict):
    # Update the score for the specified player and round.
    if data["player"] in players:
        round_index = data.get("round", len(scores[data["player"]]))
        # Ensure the score list is long enough.
        while len(scores[data["player"]]) <= round_index:
            scores[data["player"]].append(0)
        scores[data["player"]][round_index] = data["score"]
    return {"message": "Score added"}

@app.get("/reset")
async def reset_game():
    # Clear the players and scores to reset the game state.
    players.clear()
    scores.clear()
    # Redirect the user back to the home page.
    return RedirectResponse(url="/")

# Endpoint to serve the local PDF file containing the game rules.
@app.get("/rules.pdf")
async def get_rules():
    # "rules.pdf" should be located in the same directory as this script.
    return FileResponse("rules.pdf", media_type="application/pdf")

# Endpoint to serve the scoring image.
@app.get("/scoring.jpeg")
async def get_scoring_image():
    # "scoring.jpeg" should be located in the same directory as this script.
    return FileResponse("scoring.jpeg", media_type="image/jpeg")
