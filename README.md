# Soccer 5 Team Up

This script programmatically comes up with the best teams based on a yaml file
of players storing multiple skill levels . It is adapted to soccer 5 matchmaking.

## Getting started

Copy `players_example.yaml` to `players.yaml` and note your players (see below for the yaml format).

Generate a "Google OAuth Client ID" secret to be able to request google sheet api. You can store it in project root.

Copy `config_example.yaml` to `config.yaml` and fill `sheet_url` and `credentials_path` (secret file).

Launch `python3 script.py <num_teams> <num_players_per_team>` and enjoy !

## Players yaml format

The format of the yaml file must be a list of dictionaries:

    - name: <name>
      tech: <int>
      phy: <int>
      vis: <int>
      goal: <int>
    - name: <name>
      tech: <int>
      phy: <int>
      vis: <int>
      goal: <int>
    - name: <name>
      tech: <int>
      phy: <int>
      vis: <int>
      goal: <int>

I have been rating based on 1-10 but the solution should work based on any skill
rating system, as long as it remains an integer.

## Active players

Active players are retrieved from a Google Sheet. Trigrams are then compared to all player names stored in yaml file.

## Command line arguments

There are two required arguments:

    The number of teams to process the players into
    The size of each team to process the players into

Please note, the number of players must be evenly divisable by `k` and `n`.

## How is it working

### Evaluation Criteria

The program creates new team assignments based on the pool of combinations generator style.

* Profile Difference: Ensures that teams have similar technical, endurance and vision profiles. This is the primary criterion to avoid mismatches like a highly enduring team against a less enduring one.
* Score Balance: Minimizes the difference in overall scores between the teams (exclude the vision note which seems less impactful than the others).
* Variance: Keeps the variance within each team low to maintain cohesion.

### Adjustable Weights

The script uses a cost function that combines these criteria with adjustable weights:

* weight_balance: Importance of balancing overall scores.
* weight_profile: Importance of matching team profiles.
* weight_variance: Importance of minimizing intra-team variance.

These weights can be adjusted in the configuration file to prioritize different aspects of team balance.

## TODO

Develop a version (specific branch or command argument) where active players are not retrieved from a google sheet.

## Special Thank

This script was inspired by https://github.com/mas-4/teamup