import argparse
import random
import numpy as np
import yaml
from google_sheets_reader import GoogleSheetsReader

class Player:
    # Représente un joueur avec ses notes
    def __init__(self, name, tech, phy, vis, goal):
        self.name = name
        self.tech = tech
        self.phys = phy
        self.vision = vis
        self.goal = goal

    # Calcule le score total du joueur, sans vision
    def total_score(self, num_players_per_team):
        return self.tech + self.phys + (self.goal / num_players_per_team)

class Team:
    # Représente une équipe de joueurs
    def __init__(self, players=None):
        self.players = players if players else []

    # Ajoute un joueur à l'équipe
    def add_player(self, player):
        self.players.append(player)

    # Calcule le score total de l'équipe, sans vision
    def total_score(self, num_players_per_team):
        total = {
            'tech': sum(p.tech for p in self.players),
            'phys': sum(p.phys for p in self.players),
            'goal': sum(p.goal for p in self.players) / num_players_per_team
        }
        return sum(total.values())

    # Calcule la variance des scores des joueurs dans l'équipe, sans vision
    def variance(self, num_players_per_team):
        scores = [p.total_score(num_players_per_team) for p in self.players]
        return np.var(scores)

    # Calcule le profil moyen de l'équipe (technique, physique, vision) + goal pour affichage
    def profile(self):
        if not self.players:
            return 0, 0, 0, 0
        tech = sum(p.tech for p in self.players) / len(self.players)
        phys = sum(p.phys for p in self.players) / len(self.players)
        vision = sum(p.vision for p in self.players) / len(self.players)
        goal = sum(p.goal for p in self.players) / len(self.players)  # Moyenne brute, sans division par num_players_per_team
        return tech, phys, vision, goal

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
        self.vision_weight_profile = 1.0  # Poids de vision dans profile_diff

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
        # Calcule les moyennes de chaque critère pour chaque équipe
        profiles = [team.profile() for team in teams]
        cost = (self.weight_balance * balance) + (self.weight_variance * variances) + (self.weight_profile * profile_diff)
        return cost, balance, scores, variances, profile_diff, profiles

    # Calcule la différence de profil entre les équipes (sans goal)
    def _calculate_profile_difference(self, teams):
        profiles = [team.profile() for team in teams]
        differences = []
        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                tech_diff = abs(profiles[i][0] - profiles[j][0])
                phys_diff = abs(profiles[i][1] - profiles[j][1])
                vision_diff = abs(profiles[i][2] - profiles[j][2]) * self.vision_weight_profile
                differences.append(tech_diff + phys_diff + vision_diff)
        return sum(differences)

    # Trouve la meilleure répartition des équipes
    def find_best_teams(self, iterations=10000):
        best_cost = float('inf')
        best_teams = None
        best_metrics = None

        for _ in range(iterations):
            teams = self.create_teams()
            cost, balance, scores, variance, profile_diff, profiles = self.evaluate_teams(teams)
            if cost < best_cost:
                best_cost = cost
                best_teams = teams
                best_metrics = (balance, scores, variance, profile_diff, profiles)

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
        Player(p['name'], p['tech'], p['phy'], p['vis'], p['goal'])
        for p in data['players']
    ]

    # Chargement des joueurs actifs depuis Google Sheets
    sheets_reader = GoogleSheetsReader(config['sheet_url'], config['credentials_path'])
    active_player_names = sheets_reader.get_active_players()

    # Vérification des joueurs manquants dans players.yaml
    all_player_names = {p.name for p in all_players}
    missing_players = [name for name in active_player_names if name not in all_player_names]
    if missing_players:
        print(f"Erreur : Les joueurs suivants sont actifs dans Google Sheets mais absents du fichier de notation de {config['players_file_path']} : {', '.join(missing_players)}")
        return

    # Filtrage des joueurs actifs
    players = [p for p in all_players if p.name in active_player_names]

    # Vérification du nombre total de joueurs
    expected_total = args.num_teams * args.num_players_per_team
    if len(players) != expected_total:
        print(f"Erreur : Le nombre de joueurs actifs ({len(players)}) ne correspond pas au total attendu ({expected_total}) pour {args.num_teams} équipes de {args.num_players_per_team} joueurs chacune.")
        return

    # Création et équilibrage des équipes avec la config
    balancer = TeamBalancer(players, args.num_teams, args.num_players_per_team, config)
    best_teams, (balance, scores, variance, profile_diff, profiles) = balancer.find_best_teams()

    # Affichage des résultats
    print(f"Écart de score minimal entre les équipes : {balance}")
    print(f"Variance totale des équipes : {variance}")
    print("\nComparaison des profils d'équipe :")
    print(f"{'Équipe':<10} | {'Tech':>6} | {'Phys':>6} | {'Vision':>6} | {'Goal':>6}")
    print("-" * 43)
    for i, (tech, phys, vision, goal) in enumerate(profiles):
        print(f"Équipe {i + 1:<4} | {tech:>6.1f} | {phys:>6.1f} | {vision:>6.1f} | {goal:>6.1f}")

    for i, team in enumerate(best_teams):
        print(f"\nÉquipe {i + 1} (Score total: {scores[i]}):")
        for player in team.players:
            print(f"{player.name}")

if __name__ == "__main__":
    main()