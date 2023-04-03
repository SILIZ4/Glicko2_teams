from glicko import Player


def write_players(players: dict[str, Player], filename: str):
    """ Writes csv file containing players information.
    """
    with open(filename, "w") as file_stream:
        file_stream.write("#name,rating,rd,vol\n")
        for player_name, player in players.items():
            player_information = [player_name, player.rating, player.rd, player.vol]
            file_stream.write(
                ','.join(map(str, player_information))+'\n'
            )


def load_players(filename: str) -> dict[str, Player]:
    """ Reads csv file containing players information and returns
    a dictionary of the players.
    """
    players = {}
    with open(filename, "r") as file_stream:
        for line in file_stream:
            if line.startswith("#"):
                continue
            player_name, *player_stats = line.strip().split(',')

            # Initialize player with default Glicko values if player_stats empty.
            players[player_name] = Player(**dict(zip(["rating", "rd", "vol"], map(lambda x: float(x.strip()), player_stats))))
    return players


def read_games(filename: str) -> list[tuple[tuple[Player], tuple[Player], bool]]:
    """ Parses game file into a list of tuples which contain each game's information.
        Each game is a tuple (team1, team2, winning_team) where teams are tuples
        (player1_name, player2_name) for doubles are tuples (player_name) for
        singles, and where winning_team is 0 if team1 won or 1 if team2 won.
    """
    games = []
    with open(filename, "r") as file_stream:
        for i, line in enumerate(file_stream):
            if line.startswith("#"):
                continue
            *players, result = list(map(lambda x: x.strip(), line.split(',')))
            if len(players) == 2:
                games.append(((players[0]), (players[1]), int(result)))
            elif len(players) == 4:
                games.append((tuple(players[0:2]), tuple(players[2:]), int(result)))
            else:
                raise ValueError(
                    "Invalid game file: there must be 2 or 4 players per match. "
                    f"Error at line {i+1}."
                )
    return games


def apply_games(players: dict, game_filename: str):
    # Contains tuples (team_rating, opponent_rating, opponent_rd, results). Each
    # element of the tuples is a list of floats or booleans. Team ratings are
    # averaged in doubles.
    games_of_player = {player: ([], [], [], []) for player in players}
    for team1, team2, result in read_games(game_filename):
        team1_rating = Player.merge_player_ratings([players[player_name] for player_name in team1])
        team2_rating = Player.merge_player_ratings([players[player_name] for player_name in team2])
        team1_RD = Player.merge_player_RDs([players[player_name] for player_name in team1])
        team2_RD = Player.merge_player_RDs([players[player_name] for player_name in team2])

        for player_name in team1:
            games_of_player[player_name][0].append(team1_rating)
            games_of_player[player_name][1].append(team2_rating)
            games_of_player[player_name][2].append(team2_RD)
            games_of_player[player_name][3].append(result)

        for player_name in team2:
            games_of_player[player_name][0].append(team2_rating)
            games_of_player[player_name][1].append(team1_rating)
            games_of_player[player_name][2].append(team1_RD)
            games_of_player[player_name][3].append(1-result)

    for player_name, player in players.items():
        player.update_player(
            games_of_player[player_name][0],
            games_of_player[player_name][1],
            games_of_player[player_name][2],
            games_of_player[player_name][3]
        )
