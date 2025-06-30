from abstract_bot import AbstractBot
from typing import Any, List, Tuple, Dict


class ExampleBot(AbstractBot):
    """A bot that plays a trivial strategy."""

    def game_init(
        self,
        num_of_players: int,
        my_index: int,
        hand: List[Tuple[int, int]],
        kozar_card: Tuple[int, int],
        first_player: int,
        lowest_kozar: int,
    ):
        self.log("game_init called")
        ordered_suits = [0, 1, 2, 3]
        ordered_suits[self.get_kozar_suit()] = 3
        ordered_suits[3] = self.get_kozar_suit()
        # ordering the cards in an increasing order (one of a few possible orders).
        self.card_order = [(i, suit) for suit in ordered_suits for i in range(13)]

    def optional_attack(self) -> List[Tuple[int, int]]:
        for card in self.get_hand():
            for attacking_card in self.get_table_attack():
                if attacking_card[0] == card[0]:
                    self.log(f"Joining attack with: {card}")
                    return [card]
        self.log("Passing on joining attack.")
        return []


    def separate_kozars(self, cardlist: List[Tuple[int, int]]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        returns list of non-kozars, list of kozars
        """
        kozar = self.get_kozar_suit()
        nonkozars = [card for card in cardlist if card[1] != kozar]
        kozars = [card for card in cardlist if card[1] == kozar]
        return nonkozars, kozars


    def sort_cards(self, cardlist: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        nonkozars, kozars = self.separate_kozars(cardlist)
        sorted_cards = sorted(nonkozars) + sorted(kozars)
        self.log(str(sorted_cards))
        return sorted_cards


    def first_attack(self) -> List[Tuple[int, int]]:
        print(self.sort_cards(self.get_hand()))
        nonkozars, kozars = self.separate_kozars(self.get_hand())
        attack_from = nonkozars
        if not attack_from:
            attack_from = kozars
        sorted_cards = sorted(attack_from)
        attacking_card_num = sorted_cards[0][0]
        return [card for card in sorted_cards if card[0] == attacking_card_num]


    def defence(self) -> Tuple[List[Tuple[int, int]], List[int]]:
        defending_cards, indexes = [], []
        # if possible to forward
        if all(card is None for card in self.get_table_defence()):
            num = [card for card in self.get_table_attack() if card is not None][0][0]
            for card in self.get_hand():
                if card[0] == num:
                    # forward
                    self.log(f"Forwarding {card}")
                    return [card], []
        for index, attacking_card in enumerate(self.get_table_attack()):
            if attacking_card is None:
                continue
            flag: bool = False
            for card in self.get_hand():
                if self.card_order.index(attacking_card) < self.card_order.index(card):
                    defending_cards.append(card)
                    indexes.append(index)
                    flag = True
                    break
            # failed to defend
            if not flag:
                self.log("Taking cards.")
                return [], []
        self.log(f"Defending with {defending_cards}, {indexes}")
        return defending_cards, indexes

    def notify_burn(self, card_list: List[Tuple[int, int]]):
        self.log(f"burn: {card_list}")

    def notify_cards_drawn_to_hand(self, card_list: List[Tuple[int, int]]):
        self.log(f"cards drawn to hand: {card_list}")

    def notify_winner(self, winner_index: int):
        self.log(f"Winner: {winner_index}")

    def notify_pass(self, passer_index: int):
        self.log(f"Player {passer_index} passed")

    def notify_optional_attack(
        self, attacker_index: int, card_list: List[Tuple[int, int]]
    ):
        self.log(f"Player {attacker_index} optional attack with cards: {cards}")

    def notify_first_attack(
        self, attacker_index: int, card_list: List[Tuple[int, int]]
    ):
        self.log(f"Player {attacker_index} first attack with cards: {cards}")

    def notify_defence(
        self,
        defender_index: int,
        defending_cards: List[Tuple[int, int]],
        indexes: List[int],
    ):
        self.log(
            f"Player {defender_index} defended with cards: {defending_cards} at indexes: {indexes}"
        )

    def notify_forward(self, forwarder_index: int, card_list: List[Tuple[int, int]]):
        self.log(f"Player {forwarder_index} forwarded with cards: {card_list}")

    def notify_take(self, defender_index: int, card_list: List[Tuple[int, int]]):
        self.log(f"Player {defender_index} took cards: {card_list}")


bot: ExampleBot = ExampleBot()
