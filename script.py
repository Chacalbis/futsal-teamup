import argparse
import random
import numpy as np
import yaml
from google_sheets_reader import get_active_players

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
        calculate_player_total_score(player, num_players_per_team)
        for player in team
    ]
    return np.var(scores)

def calculate_team_profile(team):
    technical_score = sum(player['technicalNote'] for player in team) / len(team)
    endurance_score = sum(player['enduranceNote'] for player in team) / len(team)
    return technical_score, endurance_score

def calculate_profile_difference(teams):
    profiles = [calculate_team_profile(team) for team in teams]
    differences = []
    for i in range(len(profiles)):
        for j in range(i + 1, len(profiles)):
            tech_diff = abs(profiles[i][0] - profiles[j][0])
            endurance_diff = abs(profiles[i][1] - profiles[j][1])
            differences.append(tech_diff + endurance_diff)
    return sum(differences)

def create_teams(players, num_teams, num_players_per_team):
    random.shuffle(players)  # Mélange des joueurs pour éviter les biais
    teams = [[] for _ in range(num_teams)]
    
    for i, player in enumerate(players):
        teams[i % num_teams].append(player)
    
    return teams

def calculate_teams_balance(teams, num_players_per_team):
    scores = [calculate_team_score(team, num_players_per_team) for team in teams]
    variances = [calculate_team_variance(team, num_players_per_team) for team in teams]
    profile_difference = calculate_profile_difference(teams)
    return max(scores) - min(scores), scores, sum(variances), profile_difference

def calculate_player_total_score(player, num_players_per_team):
    return player['technicalNote'] + player['enduranceNote'] + (player['goalNote'] / num_players_per_team)

def calculate_cost(balance, variance, profile_difference, weight_balance=0.3, weight_profile=0.5, weight_variance=0.2):
    '''
    On utilise des poids pour déterminer l'importance des critères

    Critère 1 : différence de profil entre les équipes
    Critère 2 : moyenne globale entre les équipes
    Critère 3 : variance faible au sein des équipes
    '''
    return (weight_balance * balance) + (weight_profile * profile_difference) + (weight_variance * variance)

def main():
    parser = argparse.ArgumentParser(description="Créer des équipes de futsal équilibrées.")
    parser.add_argument("num_teams", type=int, help="Nombre d'équipes")
    parser.add_argument("num_players_per_team", type=int, help="Nombre de joueurs par équipe")
    args = parser.parse_args()

    # Récupération des paramètres depuis le fichier de conf
    with open("config.yaml", 'r') as config_file:
        config = yaml.safe_load(config_file)

    players_file_path = config['players_file_path']
    sheet_url = config['sheet_url']
    credentials_path = config['credentials_path']

    # Chargement des joueurs depuis le YAML
    with open(players_file_path, 'r') as file:
        data = yaml.safe_load(file)
    all_players = data['players']

    # Chargement des joueurs actifs depuis Google Sheets
    active_player_names = get_active_players(sheet_url, credentials_path)

    # Filtrage des joueurs actifs à partir de la liste complète
    players = [player for player in all_players if player['name'] in active_player_names]
    
    if len(players) != args.num_teams * args.num_players_per_team:
        print("Le nombre total de joueurs doit être égal au nombre d'équipes multiplié par le nombre de joueurs par équipe.")
        return

    best_cost = float('inf')
    best_teams = None
    
    for _ in range(10000):  # Effectuer plusieurs tentatives pour trouver la meilleure répartition
        teams = create_teams(players, args.num_teams, args.num_players_per_team)
        balance, scores, variance, profile_difference = calculate_teams_balance(teams, args.num_players_per_team)

        # Calcul du coût global
        cost = calculate_cost(balance, variance, profile_difference)

        if cost < best_cost:
            best_cost = cost
            best_teams = teams
            best_scores = scores
            best_balance = balance
            best_variance = variance
            best_profile_difference = profile_difference
    
    print(f"Écart de score minimal entre les équipes : {best_balance}")
    print(f"Variance totale des équipes : {best_variance}")
    print(f"Différence de profil entre les équipes : {best_profile_difference}")
    for i, team in enumerate(best_teams):
        print(f"\nÉquipe {i + 1} (Score total: {best_scores[i]}):")
        for player in team:
            print(f"{player['name']}")

if __name__ == "__main__":
    main()
