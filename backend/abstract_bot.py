from durak_actions import Input_actions, Output_actions
from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Dict, Optional
from time import time


class AbstractBot(ABC):
    def notify_optional_attack(
        self, attacker_index: int, card_list: List[Tuple[int, int]]
    ):
        """Info about a non-starting attack from a player."""
        pass

    def notify_first_attack(
        self, attacker_index: int, card_list: List[Tuple[int, int]]
    ):
        """Info about the starting attack from a player."""
        pass

    def notify_defence(
        self,
        defender_index: int,
        defending_cards: List[Tuple[int, int]],
        indexes: List[int],
    ):
        """Info about a defence from a player."""
        pass

    def notify_take(self, defender_index: int, card_list: List[Tuple[int, int]]):
        """Info about a player taking the attack cards to his hand."""
        pass

    def notify_forward(self, forwarder_index: int, card_list: List[Tuple[int, int]]):
        """Info about a player forwarding the attack."""
        pass

    def notify_pass(self, passer_index: int):
        """Info about a player passing (as an optional attacker)."""
        pass

    def notify_burn(self, card_list: List[Tuple[int, int]]):
        """Info about a burn of the attack cards."""
        pass

    def notify_cards_drawn_to_hand(self, card_list: List[Tuple[int, int]]):
        """Info about drawing cards from the deck to my hand."""
        pass

    def notify_winner(self, winner_index: int):
        """Info about a player who won the game."""
        pass

    def game_init(
        self,
        num_of_players: int,
        my_index: int,
        hand: List[Tuple[int, int]],
        kozar_card: Tuple[int, int],
        first_player: int,
        lowest_kozar: int,
    ):
        """Gets called when the game is initialized."""
        pass

    @abstractmethod
    def first_attack(self) -> List[Tuple[int, int]]:
        """Start an attack with a card list (mandatory)."""
        pass

    @abstractmethod
    def optional_attack(self) -> List[Tuple[int, int]]:
        """Add cards to an existing attack (optional). Return an empty list for pass."""
        pass

    @abstractmethod
    def defence(self) -> Tuple[List[Tuple[int, int]], List[int]]:
        """Defend against an attack. Return a list of cards and list of indexes
        representing which attacking card each card is defending.
        To take, return an empty list of cards and an empty list of indexes.
        To forward, return a list of forwarding cards and an empty list of indexes.
        To defend, return both lists as described above."""
        pass

    def get_hand(self) -> List[Tuple[int, int]]:
        """Get the current hand of the bot."""
        return self.__hand

    def get_kozar_suit(self) -> int:
        """Get the suit of the kozar card."""
        return self.__kozar_card[1]

    def get_kozar_card(self) -> Tuple[int, int]:
        """Get the kozar card."""
        return self.__kozar_card

    def get_table_attack(self) -> List[Optional[Tuple[int, int]]]:
        """Get the current attacking cards on the table."""
        return self.__table_attack

    def get_table_defence(self) -> List[Optional[Tuple[int, int]]]:
        """Get the current defending cards on the table."""
        return self.__table_defence

    def get_current_attacker(self) -> int:
        """Get the index of the current attacker."""
        return self.__attacker

    def get_current_defender(self) -> int:
        """Get the index of the current defender."""
        return self.__defender

    def get_my_index(self) -> int:
        """Get the index of the bot in the game."""
        return self.__my_index

    def get_num_cards_per_hand(self) -> List[int]:
        """Get the amount of cards in each hand."""
        return self.__cards_per_hand

    def get_deck_count(self) -> int:
        """Get the number of cards left in the deck."""
        return self.__deck_count

    def get_raw_events(self) -> List[Tuple]:
        """Get all the raw events that the bot has received, by order."""
        return self.__events

    def log(self, message: str):
        if isinstance(message, str):
            ts = time()
            self.__logs.append(f"[TS:{ts}]Bot {self.__my_index}: {message}")

    # Helpful for logging and debugging
    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    SUITS: List[str] = ["♣", "♦", "♥", "♠"]

    def call(
        self,
        event: Tuple,
        hand: List,
        table_attack: List,
        table_defence: List,
        cards_per_hand: List[int],
        curr_defender: int,
        deck_count: int,
        state: Dict[str, Any],
    ):
        self.__dict__.update(state if state is not None else {})
        if not hasattr(self, "_AbstractBot__events"):
            self.__events = []
        self.__events.append(event)
        action = event[0]
        self.__hand = hand
        self.__table_attack = table_attack
        self.__table_defence = table_defence
        self.__cards_per_hand = cards_per_hand
        self.__defender = curr_defender
        self.__deck_count = deck_count
        self.__logs = []
        ret_dict = {}
        match action:
            case Input_actions.OPTIONAL_ATTACK:
                cards = self.optional_attack()
                if isinstance(cards, list) and len(cards) == 0:
                    ret_dict["action"] = [Output_actions.PASS]
                else:
                    ret_dict["action"] = [Output_actions.ATTACK, cards]
            case Input_actions.FIRST_ATTACK:
                self.__attacker = self.__my_index
                cards = self.first_attack()
                ret_dict["action"] = [Output_actions.ATTACK, cards]
            case Input_actions.DEFENCE:
                cards, indexes = self.defence()
                if cards is None or len(cards) == 0:
                    ret_dict["action"] = [Output_actions.TAKE]
                elif indexes is None or len(indexes) == 0:
                    ret_dict["action"] = [Output_actions.FORWARD, cards]
                else:
                    ret_dict["action"] = [Output_actions.DEFEND, cards, indexes]
            case Input_actions.OPTIONAL_ATTACK_PASSIVE:
                self.notify_optional_attack(event[1], event[2])
            case Input_actions.FIRST_ATTACK_PASSIVE:
                self.__attacker = event[1]
                self.notify_first_attack(event[1], event[2])
            case Input_actions.DEFENCE_PASSIVE:
                self.notify_defence(event[1], event[2], event[3])
            case Input_actions.TAKE_PASSIVE:
                self.notify_take(event[1], event[2])
            case Input_actions.FORWARD_PASSIVE:
                self.notify_forward(event[1], event[2])
            case Input_actions.PASS_PASSIVE:
                self.notify_pass(event[1])
            case Input_actions.BURN:
                self.notify_burn(event[1])
            case Input_actions.TO_HAND:
                self.notify_cards_drawn_to_hand(event[1])
            case Input_actions.GAME_INIT:
                self.__my_index = event[2]
                self.__hand = event[3]
                self.__kozar_card = event[4]
                self.__attacker = event[5]
                self.game_init(
                    event[1], event[2], event[3], event[4], event[5], event[6]
                )
            case Input_actions.WINNER_PASSIVE:
                self.notify_winner(event[1])
            case _:
                raise ValueError(f"Unknown action: {action}")
        ret_dict["state"] = self.__dict__
        ret_dict["log"] = self.__logs
        return ret_dict
