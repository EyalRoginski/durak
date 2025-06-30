from abstract_bot import AbstractBot
from typing import Any, List, Tuple, Dict

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
        self.card_order = [(i, suit) for suit in ordered_suits for i in range(13)]

        # All the cards that were burned
        self.burned_cards: list[Card] = []
        # Mapping player indexes to the cards we know they have.
        self.player_cards: list[list[Card]] = [[] for _ in range(num_of_players)]
        self.player_cards[my_index] = self.sort_cards(hand)
        self.possible_cards = {(x, y) for x in range(13) for y in range(4)}
        self.my_index = my_index

        for item in hand:
            self.possible_cards.discard(item)

    def empty_deck(self):
        return self.get_deck_count() == 0

    def optional_attack(self) -> list[Card]:
        for card in self.get_hand():
            for attacking_card in self.get_table_attack():
                if not attacking_card:
                    continue
                self.possible_cards.discard(attacking_card)
                
                if attacking_card[0] == card[0] and (
                    self.empty_deck() or card[1] != self.get_kozar_suit()
                ):
                    self.log(f"Joining attack with: {card}")

                    return [card]
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
        values = sorted(set(map(lambda x:x[0], cardlist)))
        return [[y for y in cardlist if y[0]==x] for x in values]


    def first_attack(self) -> List[Card]:
        nonkozars, kozars = self.separate_kozars(self.get_hand())
        attack_from = nonkozars
        if not attack_from:
            attack_from = kozars
        sorted_cards = sorted(attack_from)
        attacking_card_num = sorted_cards[0][0]

        grouped = [g for g in self.group_by_num(sorted_cards) if len(g) > 1]
        self.log(str(grouped))
        if attacking_card_num >= 3 and grouped and grouped[0][0][0] <= 8: # no card below 5 and duplicate at most 10
            return grouped[0]

        return [card for card in sorted_cards if card[0] == attacking_card_num]
        


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

    def defence(self) -> tuple[list[Card], list[int]]:
        # if possible to forward
        if all(card is None for card in self.get_table_defence()):
            forward_list = self.possible_forward()
            if forward_list:
                # forward
                self.log(f"Forwarding with {forward_list}")
                return (forward_list, [])
        return self.defend_with_cards(self.get_hand())

    def defend_with_cards(self, hand) -> tuple[list[tuple[int, int]], list[int]]:
        defending_cards: list[Card] = []
        indexes: list[int] = []
        for index, attacking_card in enumerate(self.get_table_attack()):
            if attacking_card is None:
                continue
            flag: bool = False
            for card in self.sort_cards(hand):
                if card[0] > attacking_card[0] and card[1] == attacking_card[1]:
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
            try:
                self.player_cards[attacker_index].remove(card)
            except ValueError:
                pass
        self.log(f"Player {attacker_index} optional attack with cards: {card_list}")

    def notify_first_attack(self, attacker_index: int, card_list: list[Card]):
        for card in card_list:
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
            try:
                self.player_cards[defender_index].remove(card)
            except ValueError:
                pass
        self.log(
            f"Player {defender_index} defended with cards: {defending_cards} at indexes: {indexes}"
        )

    def notify_forward(self, forwarder_index: int, card_list: list[Card]):
        for card in card_list:
            try:
                self.player_cards[forwarder_index].remove(card)
            except ValueError:
                pass
        self.log(f"Player {forwarder_index} forwarded with cards: {card_list}")

    def notify_take(self, defender_index: int, card_list: list[Card]):
        self.player_cards[defender_index].extend(card_list)
        self.log(f"Player {defender_index} took cards: {card_list}")


bot: ExampleBot = ExampleBot()
