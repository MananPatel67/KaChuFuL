import random
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Card suits and ranks
SUITS = ['spades', 'diamonds', 'clubs', 'hearts']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

class Card:
    def __init__(self, card_id):
        self.card_id = card_id
        self.rank = card_id % 13  # 0-12
        self.suit = card_id // 13  # 0-3 (0=spades, 1=diamonds, 2=clubs, 3=hearts)
        self.selected = False
        self.face_up = True
        
    def __str__(self):
        return f"{RANKS[self.rank]}{SUITS[self.suit][0].upper()}"
    
    def get_image_key(self):
        """Returns the key to look up in card_images dictionary"""
        rank_names = {
            0: '2', 1: '3', 2: '4', 3: '5', 4: '6',
            5: '7', 6: '8', 7: '9', 8: '10',
            9: 'jack',   # Jack
            10: 'queen',  # Queen
            11: 'king',  # King
            12: 'ace'   # Ace
        }
        return f"{rank_names[self.rank]}_of_{SUITS[self.suit]}"

class Player:
    def __init__(self, name, position):
        self.name = name
        self.position = position  # 0=bottom, 1=left, 2=top, 3=right
        self.hand = []
        self.score = 0
        self.hands_won = 0
        self.bet = None
        
    def add_to_hand(self, card):
        self.hand.append(card)
        
    def play_card(self, card_index):
        if 0 <= card_index < len(self.hand):
            return self.hand.pop(card_index)
        return None

class Game:
    def __init__(self, player_names):
        logger.info(f"Initializing new game with players: {player_names}")
        self.players = [Player(name, i) for i, name in enumerate(player_names)]
        self.n_players = len(player_names)
        self.round = 0
        self.current_player = 0
        self.table = []
        self.evaluations = []
        self.trump_suit = -1
        self.state = "setup"  # setup, betting, playing, evaluating, round_over
        self.bets = [0] * self.n_players
        self.winner = None
        logger.debug("Game initialization completed")
        
    def initialize_round(self, round_num):
        logger.info(f"Initializing round {round_num}")
        self.round = round_num
        self.players = self.players[round_num-1:] + self.players[:round_num-1]
        
        # Reset round-specific attributes
        self.table = []
        self.evaluations = []
        self.current_player = 0
        self.state = "betting"
        self.trump_suit = (self.trump_suit + 1) % 4
        logger.debug(f"Round {round_num} initialized with trump suit: {self.trump_suit}")
        
        # Reset player hands and bets
        deck = [Card(i) for i in range(52)]
        random.shuffle(deck)
        
        for player in self.players:
            player.hand = []
            player.hands_won = 0
            player.bet = 0
            # Deal cards
            for _ in range(round_num):
                if deck:
                    player.add_to_hand(deck.pop())
        logger.debug(f"Cards dealt to players for round {round_num}")
        
        # Reset bets
        self.bets = [0] * self.n_players
        
    def place_bet(self, player_index, bet):
        logger.info(f"Player {player_index} placing bet: {bet}")
        if 0 <= player_index < self.n_players:
            self.bets[player_index] = bet
            self.players[player_index].bet = bet
            
            # Check if all bets are placed
            if all(b != 0 for b in self.bets):
                logger.info("All bets placed, transitioning to playing state")
                self.state = "playing"
        else:
            logger.error(f"Invalid player index for bet placement: {player_index}")
                
    def play_card(self, player_index, card_index):
        logger.info(f"Player {player_index} attempting to play card {card_index}")
        if player_index != self.current_player or self.state != "playing":
            logger.warning(f"Invalid play attempt - current player: {self.current_player}, state: {self.state}")
            return False
            
        player = self.players[player_index]
        if 0 <= card_index < len(player.hand):
            card = player.hand[card_index]
            
            # If this is not the first card played, check if player has the lead suit
            if len(self.table) > 0:
                lead_suit = self.table[0].suit
                has_lead_suit = any(c.suit == lead_suit for c in player.hand)
                
                # If player has the lead suit but didn't play it, invalid move
                if has_lead_suit and card.suit != lead_suit:
                    logger.warning(f"Player {player_index} must play lead suit {lead_suit}")
                    return False
                
                # If player doesn't have the lead suit and played a non-trump card, invalid move
                if has_lead_suit and card.suit == self.trump_suit and lead_suit!=self.trump_suit:
                    logger.warning(f"Player {player_index} must play trump suit {self.trump_suit}")
                    return False
            
            # If all checks pass, play the card
            card = player.play_card(card_index)
            if card:
                logger.info(f"Player {player_index} played {card}")
                self.table.append(card)
                
                # Evaluate card strength
                card_value = (card.rank + 26) if (card.suit == self.trump_suit) else (
                    (card.rank + 13) if len(self.table) == 0 or (self.table[0].suit == card.suit) else 0
                )
                self.evaluations.append(card_value)
                
                self.current_player = (self.current_player + 1) % self.n_players
                
                # Check if hand is complete
                if len(self.table) == self.n_players:
                    logger.info("Hand complete, evaluating...")
                    self.evaluate_hand()
                    return True
                    
                return True
        logger.warning(f"Invalid card index {card_index} for player {player_index}")
        return False
        
    def evaluate_hand(self):
        logger.info("Evaluating hand")
        if len(self.evaluations) != self.n_players:
            logger.error(f"Evaluation count mismatch: {len(self.evaluations)} != {self.n_players}")
            return
            
        # Get the lead suit (suit of first card played)
        lead_suit = self.table[0].suit
        
        # Evaluate each card's strength
        card_strengths = []
        for card in self.table:
            # If it's a trump card, it's worth rank + 26
            if card.suit == self.trump_suit:
                strength = card.rank + 26
            # If it's the lead suit, it's worth rank + 13
            elif card.suit == lead_suit:
                strength = card.rank + 13
            # Otherwise, it's worth just its rank
            else:
                strength = card.rank
            card_strengths.append(strength)
        
        # Find the winning card (highest strength)
        winning_index = card_strengths.index(max(card_strengths))
        self.players[winning_index].hands_won += 1
        logger.info(f"Hand won by player {winning_index} ({self.players[winning_index].name})")
        
        # Print evaluation info for debugging
        logger.debug("Hand evaluation results:")
        for i, (player, card, strength) in enumerate(zip(self.players, self.table, card_strengths)):
            logger.debug(f"{player.name}: {card} = {strength} ({'Trump' if card.suit == self.trump_suit else 'Lead' if card.suit == lead_suit else 'Other'})")
        
        # Check if round is over
        if all(len(player.hand) == 0 for player in self.players):
            logger.info("Round over, calculating scores")
            self.state = "round_over"
            self.calculate_scores()
        else:
            # Prepare for next hand
            logger.info("Preparing for next hand")
            self.evaluations = []
            self.table = []
            # Rotate players so winner goes first
            self.players = self.players[winning_index:] + self.players[:winning_index]
            self.bets = self.bets[winning_index:] + self.bets[:winning_index]
            self.current_player = 0
            
    def calculate_scores(self):
        logger.info("Calculating round scores")
        for player in self.players:
            if player.hands_won == player.bet:
                points = 10 * max(player.bet, 1)
                player.score += points
                logger.info(f"{player.name}: Met bet ({player.hands_won}/{player.bet}) +{points}")
            else:
                points = -10 * max(player.bet, 1)
                player.score += points
                logger.info(f"{player.name}: Missed bet ({player.hands_won}/{player.bet}) {points}")
            
            player.hands_won = 0  # Reset for next round
                
    def next_round(self):
        logger.info("Checking if next round is possible")
        if self.round < (52 // self.n_players):
            logger.info(f"Starting round {self.round + 1}")
            self.initialize_round(self.round + 1)
            return True
        logger.info("No more rounds possible")
        return False
        
    def get_valid_moves(self, player_index):
        """Return list of valid card indices that can be played"""
        player = self.players[player_index]
        valid_moves = []
        
        if len(self.table) == 0:
            # First player can play any card
            valid_moves = list(range(len(player.hand)))
        else:
            lead_suit = self.table[0].suit
            has_lead_suit = any(card.suit == lead_suit for card in player.hand)
            
            for i, card in enumerate(player.hand):
                if has_lead_suit:
                    # Must play lead suit if you have it
                    if card.suit == lead_suit:
                        valid_moves.append(i)
                else:
                    # Must play trump if you don't have lead suit
                    if card.suit == self.trump_suit:
                        valid_moves.append(i)
                        
        return valid_moves
        
    def get_valid_bets(self, player_index):
        """Return list of valid bets for the given player"""
        if player_index == len(self.players) - 1:
            # Last player can't make total bets equal to number of cards
            total_bets = sum(self.bets[:player_index])
            forbidden_bet = self.round - total_bets
            return [bet for bet in range(self.round + 1) if bet != forbidden_bet]
        else:
            # Other players can bet anything from 0 to number of cards
            return list(range(self.round + 1))
            
    def is_round_over(self):
        """Check if the current round is over"""
        return all(len(player.hand) == 0 for player in self.players)
        
    def is_game_over(self):
        """Check if the entire game is over"""
        return self.round >= (52 // self.n_players) 