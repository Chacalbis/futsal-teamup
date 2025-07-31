import argparse
import random
import numpy as np
import yaml
import requests
from google_sheets_reader import GoogleSheetsReader
from colorama import init, Fore, Style
from datetime import datetime

init()

class Player:
    def __init__(self, name, tech, phy, vis, goal):
        self.name = name
        self.tech = tech
        self.phys = phy
        self.vision = vis
        self.goal = goal

    def total_score(self, num_players_per_team):
        return self.tech + self.phys + (self.goal / num_players_per_team)

class Team:
    def __init__(self, players=None):
        self.players = players if players else []

    def add_player(self, player):
        self.players.append(player)

    def total_score(self, num_players_per_team):
        total = {
            'tech': sum(p.tech for p in self.players),
            'phys': sum(p.phys for p in self.players),
            'goal': sum(p.goal for p in self.players) / num_players_per_team
        }
        return sum(total.values())

    def variance(self, num_players_per_team):
        scores = [p.total_score(num_players_per_team) for p in self.players]
        return np.var(scores) if scores else 0

    def profile(self):
        if not self.players:
            return 0, 0, 0, 0
        tech = sum(p.tech for p in self.players) / len(self.players)
        phys = sum(p.phys for p in self.players) / len(self.players)
        vision = sum(p.vision for p in self.players) / len(self.players)
        goal = sum(p.goal for p in self.players) / len(self.players)
        return tech, phys, vision, goal

class TeamBalancer:
    def __init__(self, players, team_sizes, config):
        self.players = players
        self.team_sizes = team_sizes
        self.num_teams = len(team_sizes)
        weights = config.get('weights', {})
        self.weight_balance = weights.get('balance', 0.3)
        self.weight_variance = weights.get('variance', 0.2)
        self.weight_profile = weights.get('profile', 0.5)
        self.vision_weight_profile = 1.0

    def create_teams(self):
        shuffled_players = self.players.copy()
        random.shuffle(shuffled_players)
        teams = [Team() for _ in range(self.num_teams)]
        player_index = 0
        for i, size in enumerate(self.team_sizes):
            for _ in range(size):
                if player_index < len(shuffled_players):
                    teams[i].add_player(shuffled_players[player_index])
                    player_index += 1
        return teams

    def evaluate_teams(self, teams):
        scores = [team.total_score(len(team.players)) for team in teams]
        balance = max(scores) - min(scores)
        variances = sum(team.variance(len(team.players)) for team in teams)
        profile_diff = self._calculate_profile_difference(teams)
        profiles = [team.profile() for team in teams]
        cost = (self.weight_balance * balance) + (self.weight_variance * variances) + (self.weight_profile * profile_diff)
        return cost, balance, scores, variances, profile_diff, profiles

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

def colorize_value(value):
    if value >= 7:
        return f"{Fore.GREEN}{value:>6.1f}{Style.RESET_ALL}"
    elif value >= 5:
        return f"{Fore.YELLOW}{value:>6.1f}{Style.RESET_ALL}"
    else:
        return f"{Fore.RED}{value:>6.1f}{Style.RESET_ALL}"
    
def send_to_zulip(config, teams, scores, profiles):
    # Envoi du tirage sur Zulip dans un sujet dynamique
    zulip_config = config.get('zulip', {})
    if not all(key in zulip_config for key in ['url', 'api_key', 'email', 'stream']):
        print("Warning: Zulip configuration missing or incomplete in config.yaml. Skipping Zulip posting.")
        return

    topic = f"Foot du {datetime.now().strftime('%d/%m/%Y')} ⚽"

    # Formatage du message
    message = "**Résultats du tirage**\n\n"
    message += f"**Différence minimale entre équipes** : {scores[0] - min(scores):.1f}\n"
    message += f"**Variance totale** : {sum(team.variance(len(team.players)) for team in teams):.1f}\n\n"
    message += "**Comparaison des profils d'équipe**:\n"
    message += "```markdown\n"
    message += f"{'Équipe':<10} | {'Tech':>6} | {'Phys':>6} | {'Vision':>6} | {'Goal':>6}\n"
    message += "-" * 48 + "\n"
    for i, (tech, phys, vision, goal) in enumerate(profiles):
        message += f"Équipe {i + 1:<4} | {tech:>6.1f} | {phys:>6.1f} | {vision:>6.1f} | {goal:>6.1f}\n"
    message += "```\n\n"
    for i, team in enumerate(teams):
        message += f"**Équipe {i + 1}** ({len(team.players)} joueurs, Score total : {scores[i]:.1f}):\n"
        for player in team.players:
            message += f"- {player.name}\n"
        message += "\n"
    message += "Tirage enregistré dans l'onglet. Veuillez entrer la différence de buts manuellement après le match :pray: ."

    # Envoi du message
    url = f"{zulip_config['url']}/messages"
    data = {
        "type": "stream",
        "to": zulip_config['stream'],
        "topic": topic,
        "content": message
    }
    try:
        response = requests.post(
            url,
            data=data,
            auth=(zulip_config['email'], zulip_config['api_key'])
        )
        response.raise_for_status()
        print(f"Publié avec succès sur Zulip dans le stream '{zulip_config['stream']}' et le topic '{topic}'.")
    except requests.RequestException as e:
        print(f"Erreur lors de la publication sur Zulip : {e}")

def main():
    parser = argparse.ArgumentParser(description="Créer des équipes de futsal équilibrées.")
    parser.add_argument("--team-sizes", type=int, nargs='+', required=True, help="Tailles des équipes (ex. : 5 4)")
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
    expected_total = sum(args.team_sizes)
    if len(players) != expected_total:
        print(f"Erreur : Le nombre de joueurs actifs ({len(players)}) ne correspond pas au total attendu ({expected_total}) pour les tailles d'équipes {args.team_sizes}.")
        return

    # Création et équilibrage des équipes
    balancer = TeamBalancer(players, args.team_sizes, config)
    best_teams, (balance, scores, variance, profile_diff, profiles) = balancer.find_best_teams()

    # Affichage des résultats
    print(f"Écart de score minimal entre les équipes : {balance}")
    print(f"Variance totale des équipes : {variance}")
    print("\nComparaison des profils d'équipe :")
    print(f"{'Équipe':<10} | {'Tech':>6} | {'Phys':>6} | {'Vision':>6} | {'Goal':>6}")
    print("-" * 43)
    for i, (tech, phys, vision, goal) in enumerate(profiles):
        tech_colored = colorize_value(tech)
        phys_colored = colorize_value(phys)
        vision_colored = colorize_value(vision)
        goal_colored = colorize_value(goal)
        print(f"Équipe {i + 1:<4} | {tech_colored} | {phys_colored} | {vision_colored} | {goal_colored}")

    for i, team in enumerate(best_teams):
        print(f"\nÉquipe {i + 1} ({len(team.players)} joueurs, Score total: {scores[i]:.1f}):")
        for player in team.players:
            print(f"{player.name}")

    # Enregistrement du tirage dans l'onglet Statistiques du Google Sheet
    if len(best_teams) == 2:  # uniquement pour 2 équipes (ça devrait exclure les tournois)
        try:
            sheets_reader.save_match_result(best_teams)
        except Exception as e:
            print(f"Erreur lors de l'enregistrement dans Google Sheets : {e}")

    # Envoi sur Zulip
    send_to_zulip(config, best_teams, scores, profiles)

if __name__ == "__main__":
    main()