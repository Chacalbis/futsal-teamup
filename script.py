import yaml
import argparse
import random
import numpy as np

def load_players(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data['players']

def calculate_team_score(team, num_players_per_team):
    total_score = {
        'technicalNote': 0,
        'enduranceNote': 0,
        'goalNote': 0
    }
    for player in team:
        total_score['technicalNote'] += player['technicalNote']
        total_score['enduranceNote'] += player['enduranceNote']
        total_score['goalNote'] += player['goalNote']
    
    # Pondération du score de goal par le nombre de joueurs
    total_score['goalNote'] /= num_players_per_team
    
    return sum(total_score.values())

def calculate_team_variance(team, num_players_per_team):
    scores = [
        player['technicalNote'] + player['enduranceNote'] + (player['goalNote'] / num_players_per_team)
        for player in team
    ]
    return np.var(scores)

def create_teams(players, num_teams, num_players_per_team):
    random.shuffle(players)  # Mélanger les joueurs pour éviter les biais
    teams = [[] for _ in range(num_teams)]
    
    for i, player in enumerate(players):
        teams[i % num_teams].append(player)
    
    return teams

def calculate_teams_balance(teams, num_players_per_team):
    scores = [calculate_team_score(team, num_players_per_team) for team in teams]
    variances = [calculate_team_variance(team, num_players_per_team) for team in teams]
    return max(scores) - min(scores), scores, sum(variances)

def main():
    parser = argparse.ArgumentParser(description="Créer des équipes de futsal équilibrées.")
    parser.add_argument("file_path", help="Chemin vers le fichier YAML des joueurs")
    parser.add_argument("num_teams", type=int, help="Nombre d'équipes")
    parser.add_argument("num_players_per_team", type=int, help="Nombre de joueurs par équipe")
    args = parser.parse_args()

    players = load_players(args.file_path)
    
    if len(players) != args.num_teams * args.num_players_per_team:
        print("Le nombre total de joueurs doit être égal au nombre d'équipes multiplié par le nombre de joueurs par équipe.")
        return

    best_balance = float('inf')
    best_variance = float('inf')
    best_teams = None
    
    for _ in range(10000):  # Effectuer plusieurs tentatives pour trouver la meilleure répartition
        teams = create_teams(players, args.num_teams, args.num_players_per_team)
        balance, scores, variance = calculate_teams_balance(teams, args.num_players_per_team)
        
        if balance < best_balance or (balance == best_balance and variance < best_variance):
            best_balance = balance
            best_variance = variance
            best_teams = teams
            best_scores = scores
    
    print(f"Écart de score minimal entre les équipes : {best_balance}")
    print(f"Variance totale des équipes : {best_variance}")
    for i, team in enumerate(best_teams):
        print(f"\nÉquipe {i + 1} (Score total: {best_scores[i]}):")
        for player in team:
            print(player['name'])

if __name__ == "__main__":
    main()
