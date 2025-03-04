import argparse
import random
import numpy as np
import yaml
from google_sheets_reader import GoogleSheetsReader

class Player:
    # Représente un joueur avec ses notes
    def __init__(self, name, technical_note, endurance_note, goal_note):
        self.name = name
        self.technical_note = technical_note
        self.endurance_note = endurance_note
        self.goal_note = goal_note

    # Calcule le score total du joueur
    def total_score(self, num_players_per_team):
        return self.technical_note + self.endurance_note + (self.goal_note / num_players_per_team)

class Team:
    # Représente une équipe de joueurs
    def __init__(self, players=None):
        self.players = players if players else []

    # Ajoute un joueur à l'équipe
    def add_player(self, player):
        self.players.append(player)

    # Calcule le score total de l'équipe
    def total_score(self, num_players_per_team):
        total = {
            'technical': sum(p.technical_note for p in self.players),
            'endurance': sum(p.endurance_note for p in self.players),
            'goal': sum(p.goal_note for p in self.players) / num_players_per_team
        }
        return sum(total.values())

    # Calcule la variance des scores des joueurs dans l'équipe
    def variance(self, num_players_per_team):
        scores = [p.total_score(num_players_per_team) for p in self.players]
        return np.var(scores)

    # Calcule le profil moyen de l'équipe (technique, endurance)
    def profile(self):
        if not self.players:
            return 0, 0
        technical = sum(p.technical_note for p in self.players) / len(self.players)
        endurance = sum(p.endurance_note for p in self.players) / len(self.players)
        return technical, endurance

class TeamBalancer:
    # Gère la création et l'équilibrage des équipes
    def __init__(self, players, num_teams, num_players_per_team, config):
        self.players = players
        self.num_teams = num_teams
        self.num_players_per_team = num_players_per_team
        # Charge les poids depuis la config
        weights = config.get('weights', {})
        self.weight_balance = weights.get('balance', 0.3)
        self.weight_variance = weights.get('variance', 0.2)
        self.weight_profile = weights.get('profile', 0.5)

    # Crée des équipes aléatoires
    def create_teams(self):
        shuffled_players = self.players.copy()
        random.shuffle(shuffled_players)
        teams = [Team() for _ in range(self.num_teams)]
        for i, player in enumerate(shuffled_players):
            teams[i % self.num_teams].add_player(player)
        return teams

    # Évalue l'équilibre des équipes
    def evaluate_teams(self, teams):
        scores = [team.total_score(self.num_players_per_team) for team in teams]
        balance = max(scores) - min(scores)
        variances = sum(team.variance(self.num_players_per_team) for team in teams)
        profile_diff = self._calculate_profile_difference(teams)
        cost = (self.weight_balance * balance) + (self.weight_profile * profile_diff) + (self.weight_variance * variances)
        return cost, balance, scores, variances, profile_diff

    # Calcule la différence de profil entre les équipes
    def _calculate_profile_difference(self, teams):
        profiles = [team.profile() for team in teams]
        differences = []
        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                tech_diff = abs(profiles[i][0] - profiles[j][0])
                endurance_diff = abs(profiles[i][1] - profiles[j][1])
                differences.append(tech_diff + endurance_diff)
        return sum(differences)

    # Trouve la meilleure répartition des équipes
    def find_best_teams(self, iterations=10000):
        best_cost = float('inf')
        best_teams = None
        best_metrics = None

        for _ in range(iterations):
            teams = self.create_teams()
            cost, balance, scores, variance, profile_diff = self.evaluate_teams(teams)
            if cost < best_cost:
                best_cost = cost
                best_teams = teams
                best_metrics = (balance, scores, variance, profile_diff)

        return best_teams, best_metrics

def main():
    parser = argparse.ArgumentParser(description="Créer des équipes de futsal équilibrées.")
    parser.add_argument("num_teams", type=int, help="Nombre d'équipes")
    parser.add_argument("num_players_per_team", type=int, help="Nombre de joueurs par équipe")
    args = parser.parse_args()

    # Chargement de la configuration
    with open("config.yaml", 'r') as config_file:
        config = yaml.safe_load(config_file)

    # Chargement des joueurs depuis le YAML
    with open(config['players_file_path'], 'r') as file:
        data = yaml.safe_load(file)
    all_players = [
        Player(p['name'], p['technicalNote'], p['enduranceNote'], p['goalNote'])
        for p in data['players']
    ]

    # Chargement des joueurs actifs depuis Google Sheets
    sheets_reader = GoogleSheetsReader(config['sheet_url'], config['credentials_path'])
    active_players = sheets_reader.get_active_players()
    players = [p for p in all_players if p.name in active_players]

    # Vérification du nombre de joueurs
    if len(players) != args.num_teams * args.num_players_per_team:
        print("Le nombre total de joueurs doit être égal au nombre d'équipes multiplié par le nombre de joueurs par équipe.")
        return

    # Création et équilibrage des équipes avec la config
    balancer = TeamBalancer(players, args.num_teams, args.num_players_per_team, config)
    best_teams, (balance, scores, variance, profile_diff) = balancer.find_best_teams()

    # Affichage des résultats
    print(f"Écart de score minimal entre les équipes : {balance}")
    print(f"Variance totale des équipes : {variance}")
    print(f"Différence de profil entre les équipes : {profile_diff}")
    for i, team in enumerate(best_teams):
        print(f"\nÉquipe {i + 1} (Score total: {scores[i]}):")
        for player in team.players:
            print(f"{player.name}")

if __name__ == "__main__":
    main()