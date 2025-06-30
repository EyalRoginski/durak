from itertools import combinations
from abstract_bot import AbstractBot
from typing import Any, List, Tuple, Dict

from configurations import CARDS_PER_HAND

Card = tuple[int, int]


class ExampleBot(AbstractBot):
    """A bot that plays a trivial strategy."""

    def game_init(
        self,
        num_of_players: int,
        my_index: int,
        hand: list[Card],
        kozar_card: Card,
        first_player: int,
        lowest_kozar: int,
    ):
        self.log("game_init called")
        ordered_suits = [0, 1, 2, 3]
        ordered_suits[self.get_kozar_suit()] = 3
        ordered_suits[3] = self.get_kozar_suit()
        # ordering the cards in an increasing order (one of a few possible orders).
        self.card_order: list[Card] = [
            (i, suit) for suit in ordered_suits for i in range(13)
        ]

        # All the cards that were burned
        self.burned_cards: list[Card] = []
        # Mapping player indexes to the cards we know they have.
        self.player_cards: list[list[Card]] = [[] for _ in range(num_of_players)]
        self.player_cards[my_index] = self.sort_cards(hand)
        self.possible_cards: set[Card] = {(x, y) for x in range(13) for y in range(4)}
        self.my_index: int = my_index

        for item in hand:
            self.possible_cards.discard(item)

    def strength(self, card: Card) -> float:
        return card[0] + (7.0 if card[1] == self.get_kozar_suit() else 0.0)

    def get_average_strength(self) -> float:
        return sum(self.strength(card) for card in self.possible_cards) / len(
            self.possible_cards if self.possible_cards else 0
        )

    def evaluate(self, hand: list[Card]) -> float:
        drawn_cards = (
            len(hand) if self.empty_deck() else max(0, CARDS_PER_HAND - len(hand))
        )
        score: float = (
            sum(self.strength(card) for card in hand)
            + self.get_average_strength() * drawn_cards
        ) / (float(len(hand) + drawn_cards) ** 2.0)
        score += max(0, len(hand) + drawn_cards - CARDS_PER_HAND) * -20.0
        return score

    def empty_deck(self):
        return self.get_deck_count() == 0

    """def optional_attack(self) -> list[Card]:
    def optional_attack(self) -> list[Card]:
        if self.get_table_attack()[-1] != None:
            return []  # full attack
        attacking_cards = []
        for card in self.get_hand():
            for attacking_card in self.get_table_attack() + self.get_table_defence():
                if not attacking_card:
                    continue
                self.possible_cards.discard(attacking_card)

                if attacking_card[0] == card[0] and (
                    self.empty_deck() or card[1] != self.get_kozar_suit()
                ):
                    self.log(f"Joining attack with: {card}")

                    attacking_cards.append(card)
        self.log("Passing on joining attack.")
        return []"""

    def optional_attack_options(self, cardlist: List[Card]) -> List[Card]:
        options: List[Card] = []
        for card in cardlist:
            for table_card in self.get_table_attack() + self.get_table_defence():
                if not table_card:
                    continue
                if table_card[0] == card[0]:
                    options.append(card)
        return self.non_empty_subsets(options)

    def optional_attack(self) -> List[Card]:
        if self.get_table_attack()[-1] != None:
            return []  # full attack
        options: List[Card] = self.optional_attack_options(self.get_hand())
        options.append([])
        best_option: List[Card] = max(
            options,
            key=lambda x: self.evaluate(list(set(self.get_hand()) - set(x))),
            default=[],
        )
        scores = [
            self.evaluate(list(set(self.get_hand()) - set(option)))
            for option in options
            ]
        self.log(f"Options: {options}, scores: {scores}")
        if best_option:
            self.log(f"Joining attack with: {best_option}")
            return list(best_option)
        self.log("Passing on joining attack.")
        return []

    def separate_kozars(self, cardlist: List[Card]) -> Tuple[List[Card], List[Card]]:
        """
        returns list of non-kozars, list of kozars
        """
        kozar = self.get_kozar_suit()
        nonkozars = [card for card in cardlist if card[1] != kozar]
        kozars = [card for card in cardlist if card[1] == kozar]
        return nonkozars, kozars

    def get_kozars_sorted(self) -> list[tuple[int, int]]:
        """
        Returns the kozars in sorted order.
        """
        kozars = self.separate_kozars(self.get_hand())[1]
        return sorted(kozars, key=lambda x: x[0])

    def sort_cards(self, cardlist: List[Card]) -> List[Card]:
        nonkozars, kozars = self.separate_kozars(cardlist)
        sorted_cards = sorted(nonkozars) + sorted(kozars)
        self.log(str(sorted_cards))
        return sorted_cards

    def group_by_num(self, cardlist: List[Card]) -> List[List[Card]]:
        values = sorted(set(map(lambda x: x[0], cardlist)))
        return [[y for y in cardlist if y[0] == x] for x in values]

    """def first_attack(self) -> List[Card]:
        nonkozars, kozars = self.separate_kozars(self.get_hand())
        attack_from = nonkozars
        if not attack_from:
            attack_from = kozars
        sorted_cards = sorted(attack_from)
        attacking_card_num = sorted_cards[0][0]

        grouped = [g for g in self.group_by_num(sorted_cards) if len(g) > 1]
        self.log(str(grouped))
        if (
            attacking_card_num >= 3 and grouped and grouped[0][0][0] <= 8
        ):  # no card below 5 and duplicate at most 10
            return grouped[0]

        return [card for card in sorted_cards if card[0] == attacking_card_num]"""

    def first_attack(self) -> List[Card]:
        options: List[Card] = sum([
            self.non_empty_subsets(g)
            for g in self.group_by_num(self.get_hand())
            ], [])
        best_option: List[Card] = max(
            options,
            key=lambda x: self.evaluate(list(set(self.get_hand()) - set(x))),
            default=[],
        )
        scores = [
            self.evaluate(list(set(self.get_hand()) - set(option)))
            for option in options
        ]
        self.log(f"Options: {options}, scores: {scores}")
        self.log(f"Attacking with: {best_option}")
        return list(best_option)

    def possible_forward(self) -> list[Card]:
        """
        If we can forward without a kozar, return the list representing the
        cards we forward with (currently just one)
        """
        num = [card for card in self.get_table_attack() if card is not None][0][0]
        attacking_cards = []
        for card in self.get_hand():
            if card[0] == num and card[1] != self.get_kozar_suit():
                attacking_cards.append(card)
        return attacking_cards

    def non_empty_subsets(self, l: list[Any]) -> list[list[Any]]:
        result: list[list[Any]] = []
        for r in range(1, len(l) + 1):
            result.extend(list(combinations(l, r)))
        return result

    def all_possible_forwards(self) -> list[list[Card]]:
        num = [card for card in self.get_table_attack() if card is not None][0][0]
        forwarding_cards: list[Card] = []
        for card in self.get_hand():
            if card[0] == num:
                forwarding_cards.append(card)
        return self.non_empty_subsets(forwarding_cards)

    def defence(self) -> tuple[list[Card], list[int]]:
        # if possible to forward
        forward_lists = self.all_possible_forwards()
        defence_list = self.defend_with_cards(self.get_hand())
        self.log(f"All possible forwards: {forward_lists}")

        best_forward = max(
            forward_lists,
            key=lambda cards: self.evaluate(
                list(set(self.get_hand()) - set(cards))
            ),  # Hand after forward
            default=None,
        )

        forward_score = (
            self.evaluate(list(set(self.get_hand()) - set(best_forward)))
            if best_forward
            else -1000.0
        )
        self.log(f"Best forward: {best_forward}; score: {forward_score}")

        defence_score = (
            self.evaluate(list(set(self.get_hand()) - set(defence_list[0])))
            if defence_list[0]
            else -1000.0
        )
        self.log(f"Defence: {defence_list}; score: {defence_score}")

        attacking_cards = list(
            filter(lambda card: card is not None, self.get_table_attack())
        )
        take_score = self.evaluate(self.get_hand() + attacking_cards)
        self.log(f"Take score: {take_score}")

        max_score = max([take_score, defence_score, forward_score])
        if max_score == take_score:
            self.log(f"Taking")
            return [], []
        if max_score == defence_score:
            self.log(f"Defending")
            return defence_list
        if max_score == forward_score:
            self.log(f"Forwarding")
            return list(best_forward), []

    def defend_with_cards(
        self, hand: list[Card]
    ) -> tuple[list[tuple[int, int]], list[int]]:
        defending_cards: list[Card] = []
        indexes: list[int] = []
        current_defence = self.get_table_defence()
        for index, attacking_card in enumerate(self.get_table_attack()):
            if attacking_card is None:
                continue
            if current_defence[index]:  # already defended this one
                continue
            flag: bool = False
            for card in self.sort_cards(hand):
                if (
                    card[0] > attacking_card[0] and card[1] == attacking_card[1]
                ) or card[1] == self.get_kozar_suit():
                    defending_cards.append(card)
                    indexes.append(index)
                    hand.remove(card)
                    flag = True
                    break
            # failed to defend
            if not flag:
                kozars = self.get_kozars_sorted()
                if self.empty_deck() and kozars:
                    defending_cards.append(kozars[0])
                    indexes.append(index)
                    hand.remove(kozars[0])
                else:
                    self.log("Taking cards.")
                    return [], []
        self.log(f"Defending with {defending_cards}, {indexes}")
        return defending_cards, indexes

    def notify_burn(self, card_list: list[Card]):
        self.log(f"burn: {card_list}")
        self.burned_cards.extend(card_list)

    def notify_cards_drawn_to_hand(self, card_list: list[Card]):
        self.log(f"cards drawn to hand: {card_list}")

    def notify_winner(self, winner_index: int):
        self.log(f"Winner: {winner_index}")

    def notify_pass(self, passer_index: int):
        self.log(f"Player {passer_index} passed")

    def notify_optional_attack(self, attacker_index: int, card_list: list[Card]):
        for card in card_list:
            self.possible_cards.discard(card)
            try:
                self.player_cards[attacker_index].remove(card)
            except ValueError:
                pass
        self.log(f"Player {attacker_index} optional attack with cards: {card_list}")

    def notify_first_attack(self, attacker_index: int, card_list: list[Card]):
        for card in card_list:
            self.possible_cards.discard(card)
            try:
                self.player_cards[attacker_index].remove(card)
            except ValueError:
                pass

        self.log(f"Player {attacker_index} first attack with cards: {card_list}")

    def notify_defence(
        self,
        defender_index: int,
        defending_cards: list[Card],
        indexes: list[int],
    ):
        for card in defending_cards:
            self.possible_cards.discard(card)
            try:
                self.player_cards[defender_index].remove(card)
            except ValueError:
                pass
        self.log(
            f"Player {defender_index} defended with cards: {defending_cards} at indexes: {indexes}"
        )

    def notify_forward(self, forwarder_index: int, card_list: list[Card]):
        for card in card_list:
            self.possible_cards.discard(card)
            try:
                self.player_cards[forwarder_index].remove(card)
            except ValueError:
                pass
        self.log(f"Player {forwarder_index} forwarded with cards: {card_list}")

    def notify_take(self, defender_index: int, card_list: list[Card]):
        self.player_cards[defender_index].extend(card_list)
        self.log(f"Player {defender_index} took cards: {card_list}")


bot: ExampleBot = ExampleBot()
