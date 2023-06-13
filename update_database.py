from os import path

from database import apply_games, write_players, load_players

RATINGS_FILE_NAME = "ratings.csv"
NEW_RATINGS_FILE_NAME = "new_ratings.csv"
GAMES_FILE_NAME = "games.csv"

if __name__ == "__main__":
    if not path.isfile(RATINGS_FILE_NAME):
        raise ValueError(
            "No rating file found. Ratings must be initilized before using this script."
        )

    if not path.isfile(GAMES_FILE_NAME):
        raise ValueError("No games file found.")

    players = load_players(RATINGS_FILE_NAME)
    apply_games(players, GAMES_FILE_NAME)
    write_players(players, NEW_RATINGS_FILE_NAME)
