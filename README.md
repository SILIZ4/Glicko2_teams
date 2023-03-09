# Glicko for teams

Python implementation of Glicko-2 rating system derived from [ryankirkman](https://github.com/ryankirkman/pyglicko2)'s implementation.

## Usage

Create a file `ratings.csv` with each player name and a file `games.csv`. Then, run the script
```
python update_database.py
```
The new ratings are in the file `new_ratings.csv`

The files handled by this script are of type `.csv`, which means they can be handled by hand or by a standard spreadsheet software.

## Games file

The games file has the format
```
team1 member1,[team1 member2,]team2 member1,[team2 member2,]winning team
John,Joe,Ben,Ash,0
Ash,Ben,1
...
```
Each line (past the first one) is either a singles or doubles game. The `winning team` must be 0 if the first team won and 1 if the second team won.

In this example the first line is a doubles match between John and Joe vs Ben and Ash where John and Joe won. The second line of the example is a singles game between Ash and Ben which Ben won.

Each player name in the games file must exist in the `ratings.csv` file.

## Ratings file

The ratings file has the format
```
name,rating,rd,vol
Ash,1800,200,0.0
Ben,1400,100,0.06
John
Joe,1600,100,0.06
...
```
Each line contains the player's name, rating, rating uncertainty (RD) and volatility (vol). A line may have only contain a name, which means that the player is not rated. In this case, the player's rating is initialized with default values `rating=1500`, `rd=350` and `vol=0.06`. Since this is a `.csv` file, the decimal values __must be written with dots__ (and not commas).

In this example, Ash has a rating of 1800 with uncertainty 200 and volatility 0.06. John is not rated.

## Glicko-2 adjustment for doubles

The rating formula of Glicko-2 can only handle singles. Considering the rating as a normal random variable of expectation $r$ (rating) and variance $RD^2$ (uncertainty), the rating average of the team is $(r_1+r_2)/2$ with uncertainty $\sqrt{RD_1^2 + RD_2^2}$, where the indices $1$ and $2$ are the players $1$ and $2$ of the team.

The result of a game is considered a singles match between the average ratings of the team. This means that in each sum on the games in the Glicko-2 formulae, the rating of the player is replaced by the average rating of the doubles team for that particular game instead of being the player's rating.
