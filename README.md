# Soccer 5 Team Up

This script generates balanced teams for soccer 5 (futsal) matchmaking based on player skill levels stored in a YAML file. It retrieves active players from a Google Sheet and optimizes team assignments using customizable criteria.

## Getting started

1. **Configure Player Data**:
   - Copy `players_example.yaml` to `players.yaml`.
   - Edit `players.yaml` to include your players in the following format:
```yaml
    - name: <string>
      tech: <int>
      phy: <int>
      vis: <int>
      goal: <int>
    - name: <string>
      tech: <int>
      phy: <int>
      vis: <int>
      goal: <int>
    - [...]
```
I have been rating based on 1-10 but the solution should work based on any skill
rating system, as long as it remains an integer.

2. **Set Up Google Sheets**:
  Create a Google Sheet with:
    - A sheet for active players
    - An optional "MatchHistory" sheet to store match results (auto-created by the script).
  Note: Player trigrams in the Google Sheet must match those in `players.yaml`.

3. **Set Up a Google Service Account**:
   - Go to the Google Cloud Console.
   - Create or select a project.
   - Enable the "Google Sheets API" in "APIs & Services" > "Library".
   - Create a Service Account in "APIs & Services" > "Credentials":
     - Name: e.g., `futsal-teamup-service-account`.
     - Skip optional steps and click "Done".
   - Generate a JSON key:
     - In the Service Account’s "Keys" tab, select "Add Key" > "Create new key" > "JSON".
     - Download and rename the file to `service_account.json`.
     - Place it in the project directory.
   - Share the Google Sheet with the Service Account’s email (found in `service_account.json` under client_email, e.g., `futsal-teamup-service-account@your-project.iam.gserviceaccount.com`) with "Editor" permissions.

4. **Configure the Application**:
   - Copy `config_example.yaml` to `config.yaml`.
   - Update `config.yaml` with:
    ```yaml
      sheet_url: "https://docs.google.com/spreadsheets/d/your-sheet-id"
      credentials_path: "service_account.json"
      players_file_path: "players.yaml"
      weights:
        balance: 0.3
        variance: 0.2
        profile: 0.5
    ```

5. **Run the Script**:
   - Locally:
    ```bash
      pip install numpy pyyaml gspread oauth2client colorama
      python script.py --team-sizes 5 5
    ```
   - With Docker (recommanded):
    ```bash
      docker build -t futsal-teamup .
      docker run --rm -v $(pwd):/app futsal-teamup python script.py --team-sizes 5 5
    ```

## Command Line Arguments
The script requires the --team-sizes argument, specifying the number of players per team.
The total number of active players (from the Google Sheet) must equal the sum of team sizes, number of players of each team may not be equal though (e.g., 9 for `--team-sizes 5 4`).


## How it works

### Evaluation Criteria

The script generates teams by optimizing:

* **Profile Difference**: Ensures that teams have similar technical, endurance and vision profiles. This is the primary criterion to avoid mismatches like a highly enduring team against a less enduring one.
* **Score Balance**: Minimizes the difference in overall scores between the teams (exclude the vision note which seems less impactful than the others).
* **Variance**: Keeps intra-team variance low for cohesive teams.

### Adjustable Weights

A cost function combines these criteria with configurable weights:

* `weight_balance`: Importance of balancing overall scores.
* `weight_profile`: Importance of matching team profiles.
* `weight_variance`: Importance of minimizing intra-team variance.

These weights can be adjusted in `config.yaml` to prioritize different aspects of team balance.

## Match history and statistics
- The script writes match results to the "MatchHistory" sheet in Google Sheets (Match ID, Date, Team 1 Players, Team 2 Players, Goal Difference (Team 1)).
- Manually enter the goal difference (e.g., 3 or -5) after each match.
- Then you can easily create a "WinRates" sheet to track players' win percentages and performance using Google Sheets formulas.

## TODO

Develop a version (specific branch or command argument) without any google sheet dependance.

## Credits

This script was inspired by https://github.com/mas-4/teamup