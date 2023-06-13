"""
Copyright (c) 2009 Ryan Kirkman

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import math


class Player:

    def __init__(self, rating=1500, rd=350, vol=0.06):
        self.setRating(rating)
        self.setRd(rd)
        self.vol = vol

    def getRating(self) -> float:
        return (self.__rating * 173.7178) + 1500

    def setRating(self, rating: float):
        self.__rating = (rating - 1500) / 173.7178

    rating = property(getRating, setRating)

    def getRd(self) -> float:
        return self.__rd * 173.7178

    def setRd(self, rd: float):
        self.__rd = rd / 173.7178

    rd = property(getRd, setRd)

    def update_player(self, team_ratings: list[float],
                      opponent_ratings: list[float], opponent_RDs: list[float],
                      outcome_list: list[int]):
        """ Calculate the new rating and rating deviation of the player for the given
            games in outcome_list.
        """
        if len(outcome_list) == 0:  # Player did not play any match
            self.__rd = Glicko2.pre_rating_RD(self.vol, self.__rd)
            self.rd = Player._bound_RD(self.rd)
            return

        # Convert the rating and rating deviation values for internal use.
        team_ratings = Glicko2.convert_ratings(team_ratings)
        opponent_ratings = Glicko2.convert_ratings(opponent_ratings)
        opponent_RDs = Glicko2.convert_RDs(opponent_RDs)

        v = Glicko2.v(team_ratings, opponent_ratings, opponent_RDs)
        delta = Glicko2.delta(team_ratings, opponent_ratings, opponent_RDs,
                              outcome_list, v)
        self.vol = Glicko2.newVol(self.rating, self.__rd, self.vol, v, delta)

        self.__rd = Glicko2.pre_rating_RD(self.vol, self.__rd)
        self.__rd = Glicko2.new_RD(self.__rd, v)
        self.rd = Player._bound_RD(self.rd)

        self.__rating += Glicko2.rating_diff(self.__rd, team_ratings,
                                             opponent_ratings, opponent_RDs,
                                             outcome_list)

    @staticmethod
    def merge_player_ratings(players: list) -> float:
        """ Average players' ratings.
        """
        if len(players) == 1:
            return players[0].rating
        return sum(map(lambda x: x.rating, players)) / len(players)

    @staticmethod
    def merge_player_RDs(players: list) -> float:
        """ Combine players' RD by assuming the ratings are normal distributions
            of variance RD^2.
        """
        if len(players) == 1:
            return players[0].rd
        return math.sqrt(sum(map(lambda x: x.rd**2, players)))

    @staticmethod
    def _bound_RD(RD: float) -> float:
        """ Bound RD in [30, 350] to avoid drastic variations in rating_diff
            and to make sure player's rating doesn't stagnate.
        """
        if RD < 30:  # Minimum threshold suggested by Glickman
            return 30
        if RD > 350:  # RD cap at 350
            return 350
        return RD

    def __repr__(self) -> str:
        return f"Player of rating {self.rating}, RD {self.rd} and of vol {self.vol}."


class Glicko2:
    _tau = 0.5

    @staticmethod
    def convert_ratings(ratings: list[float]) -> list[float]:
        """ Rescale ratings to values used for the update.
        """
        return [(x - 1500) / 173.7178 for x in ratings]

    @staticmethod
    def convert_RDs(RDs: list[float]) -> list[float]:
        """ Rescale RDs to values used for the update.
        """
        return [x / 173.7178 for x in RDs]

    @staticmethod
    def rating_diff(RD: float, team_ratings: list[float],
                    opponent_ratings: list[float], opponent_RDs: list[float],
                    outcome_list: list[int]) -> float:
        """ Compute the increment of rating for the player.
        """
        return math.pow(RD, 2) * sum(
            map(Glicko2._rating_diff_element, team_ratings, opponent_ratings,
                opponent_RDs, outcome_list))

    @staticmethod
    def _rating_diff_element(team_rating: float, opponent_rating: float,
                             opponent_RD: float, outcome: int) -> float:
        return Glicko2.g(opponent_RD)\
            * (outcome - Glicko2.E(team_rating, opponent_rating, opponent_RD))

    @staticmethod
    def pre_rating_RD(vol: float, RD: float) -> float:
        """ Calculate and update the player's rating deviation for the
            beginning of a rating period.
        """
        return math.sqrt(math.pow(RD, 2) + math.pow(vol, 2))

    @staticmethod
    def new_RD(RD: float, v: float) -> float:
        """ Compute the new RD of player.
        """
        return 1 / math.sqrt((1 / math.pow(RD, 2)) + (1 / v))

    @staticmethod
    def delta(team_ratings: list[float], opponent_ratings: list[float],
              opponent_RDs: list[float], outcome_list: list[int],
              v: float) -> float:
        """ The delta function of the Glicko2 system.
        """
        return v * sum(
            map(Glicko2._delta_element, team_ratings, opponent_ratings,
                opponent_RDs, outcome_list))

    @staticmethod
    def _delta_element(team_rating: float, opponent_rating: float,
                       opponent_RD: float, outcome: int) -> float:
        return Glicko2.g(opponent_RD)\
            * (outcome - Glicko2.E(team_rating, opponent_rating, opponent_RD))

    @staticmethod
    def v(team_ratings: list[float], opponent_ratings: list[float],
          opponent_RDs: list[float]) -> float:
        """ The v function of the Glicko2 system.
        """
        return 1 / sum(
            map(Glicko2._v_element, team_ratings, opponent_ratings,
                opponent_RDs))

    @staticmethod
    def _v_element(team_rating: float, opponent_rating: float,
                   opponent_RD: float) -> float:
        E_value = Glicko2.E(team_rating, opponent_rating, opponent_RD)
        return math.pow(Glicko2.g(opponent_RD), 2) * E_value * (1 - E_value)

    @staticmethod
    def E(team_rating: float, opponent_rating: float,
          opponent_RD: float) -> float:
        """ The Glicko E function.
        """
        return 1 / (1 + math.exp(-Glicko2.g(opponent_RD) *
                                 (team_rating - opponent_rating)))

    @staticmethod
    def g(RD: float) -> float:
        """ The Glicko2 g(RD) function.
        """
        return 1 / math.sqrt(1 + 3 * math.pow(RD, 2) / math.pow(math.pi, 2))

    @staticmethod
    def newVol(rating: float, RD: float, vol: float, v: float,
               delta: float) -> float:
        """ Calculate the new volatility as per the Glicko2 system (Feb 22 2012 revision).
        """
        #step 1
        a = 2 * math.log(vol)
        eps = 1e-6
        A = a
        tau_2 = Glicko2._tau * Glicko2._tau
        f = lambda x: Glicko2.f(x, rating, delta, v, a)

        #step 2
        B = None
        if (delta * delta) > (RD * RD + v):
            B = math.log(delta * delta - RD * RD - v)
        else:
            k = 1
            while f(a - k * math.sqrt(tau_2)) < 0:
                k = k + 1
            B = a - k * math.sqrt(tau_2)

        #step 3
        fA = f(A)
        fB = f(B)

        #step 4
        while math.fabs(B - A) > eps:
            #a
            C = A + ((A - B) * fA) / (fB - fA)
            fC = f(C)
            #b
            if fC * fB < 0:
                A = B
                fA = fB
            else:
                fA = fA / 2.0
            #c
            B = C
            fB = fC

        #step 5
        return math.exp(A / 2)

    @staticmethod
    def f(x: float, rating: float, delta: float, v: float, a: float) -> float:
        ex = math.exp(x)
        num1 = ex * (delta * delta - rating * rating - v - ex)
        denom1 = 2 * ((rating * rating + v + ex)**2)
        return (num1 / denom1) - ((x - a) / (Glicko2._tau**2))
