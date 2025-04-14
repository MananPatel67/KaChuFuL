import os
import sys
import pygame
from pygame.locals import *
import math
import logging
import random
import time
from game_logic import Game, SUITS, RANKS

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

# Initialize pygame
pygame.init()
pygame.font.init()
logger.info("Pygame initialized successfully")

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
CARD_WIDTH = 80
CARD_HEIGHT = 120

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)  # Forest Green
DARK_GREEN = (0, 100, 0)
RED = (220, 20, 60)  # Crimson
BLUE = (30, 144, 255)  # Dodger Blue
GRAY = (169, 169, 169)  # Dark Gray
GOLD = (255, 215, 0)  # Gold
SILVER = (192, 192, 192)  # Silver

# Fonts
FONT_SMALL = pygame.font.Font(None, 24)
FONT_MEDIUM = pygame.font.Font(None, 32)
FONT_LARGE = pygame.font.Font(None, 48)
FONT_TITLE = pygame.font.Font(None, 64)

class KachufulGame:
    def __init__(self):
        logger.info("Initializing KachufulGame")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Kachuful Card Game")
        self.clock = pygame.time.Clock()
        self.card_images = {}
        self.load_card_images()
        self.game = None
        self.selected_card = None
        self.player_names = ["Player 1", "Player 2", "Player 3", "Player 4"][:3]  # Default to 3 players
        self.name_input = ""
        self.active_input = 0
        self.showing_turn_screen = False  # Flag for turn transition screen
        self.submitted_bets = []  # List to track which players have submitted bets
        logger.info("KachufulGame initialization completed")
        
    def load_card_images(self):
        logger.info("Loading card images")
        try:
            card_dir = "PNG"
            
            # Mapping between rank indices and filenames
            rank_files = {
                0: '2', 1: '3', 2: '4', 3: '5', 4: '6',
                5: '7', 6: '8', 7: '9', 8: '10',
                9: 'jack',   # Jack
                10: 'queen',  # Queen
                11: 'king',  # King
                12: 'ace'   # Ace
            }
            
            # Load all card images
            for suit_idx, suit in enumerate(SUITS):
                for rank_idx in range(13):
                    file_rank = rank_files[rank_idx]
                    image_name = f"{file_rank}_of_{suit}.png"
                    image_path = os.path.join(card_dir, image_name)
                    
                    if os.path.exists(image_path):
                        image = pygame.image.load(image_path)
                        # Scale down the images to our card size
                        self.card_images[f"{file_rank}_of_{suit}"] = pygame.transform.scale(
                            image, (CARD_WIDTH, CARD_HEIGHT))
                    else:
                        logger.warning(f"Missing image: {image_path}")
            
            # Load back image
            back_path = os.path.join(card_dir, "back.png")
            if os.path.exists(back_path):
                self.card_back = pygame.transform.scale(
                    pygame.image.load(back_path), (CARD_WIDTH, CARD_HEIGHT))
            else:
                logger.warning("Missing back image, creating placeholder")
                # Create simple back if image missing
                self.card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
                self.card_back.fill(BLUE)
                pygame.draw.rect(self.card_back, RED, (5, 5, CARD_WIDTH-10, CARD_HEIGHT-10), 3)
                
        except Exception as e:
            logger.error(f"Error loading images: {e}")
            # Create placeholder cards if images fail to load
            self.create_placeholder_cards()
            
    def draw_card(self, card, x, y, highlight=False):
        """Draw a card at the specified position"""
        if card.face_up:
            image_key = card.get_image_key()
            if image_key in self.card_images:
                self.screen.blit(self.card_images[image_key], (x, y))
            else:
                # Fallback if image not found - should only happen if loading failed
                pygame.draw.rect(self.screen, WHITE, (x, y, CARD_WIDTH, CARD_HEIGHT))
                pygame.draw.rect(self.screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT), 2)
                text = FONT_MEDIUM.render(str(card), True, BLACK)
                self.screen.blit(text, (x + 10, y + 50))
        else:
            self.screen.blit(self.card_back, (x, y))
            
        if highlight:
            pygame.draw.rect(self.screen, RED, (x-2, y-2, CARD_WIDTH+4, CARD_HEIGHT+4), 3)
            
    def draw_rounded_rect(self, surface, color, rect, radius=10):
        """Draw a rounded rectangle"""
        pygame.draw.rect(surface, color, rect, border_radius=radius)

    def draw_text_with_shadow(self, text, font, color, x, y, shadow_color=BLACK, shadow_offset=2):
        """Draw text with a shadow effect"""
        shadow = font.render(text, True, shadow_color)
        surface = font.render(text, True, color)
        self.screen.blit(shadow, (x + shadow_offset, y + shadow_offset))
        self.screen.blit(surface, (x, y))

    def draw_setup_screen(self):
        """Draw the player setup screen"""
        self.screen.fill(GREEN)
        
        title = FONT_TITLE.render("Kachuful Card Game", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        instructions = FONT_MEDIUM.render("Enter player names (comma separated):", True, WHITE)
        self.screen.blit(instructions, (SCREEN_WIDTH//2 - instructions.get_width()//2, 150))
        
        # Input box
        pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH//2 - 200, 200, 400, 40))
        input_text = FONT_MEDIUM.render(self.name_input, True, BLACK)
        self.screen.blit(input_text, (SCREEN_WIDTH//2 - 190, 210))
        
        # Start button
        pygame.draw.rect(self.screen, BLUE, (SCREEN_WIDTH//2 - 100, 300, 200, 50))
        start_text = FONT_MEDIUM.render("Start Game", True, WHITE)
        self.screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 315))
        
        pygame.display.flip()
        
    def draw_betting_screen(self):
        self.screen.fill(DARK_GREEN)
        
        # Draw a decorative border
        pygame.draw.rect(self.screen, GOLD, (10, 10, SCREEN_WIDTH-20, SCREEN_HEIGHT-20), 3, border_radius=15)
        
        # Round and trump info with shadow
        round_text = FONT_TITLE.render(f"Round {self.game.round}", True, GOLD)
        self.draw_text_with_shadow(f"Round {self.game.round}", FONT_TITLE, GOLD, 
                                 SCREEN_WIDTH//2 - round_text.get_width()//2, 20)
        
        trump_text = FONT_MEDIUM.render(f"Trump Suit: {SUITS[self.game.trump_suit].capitalize()}", True, SILVER)
        self.draw_text_with_shadow(f"Trump Suit: {SUITS[self.game.trump_suit].capitalize()}", FONT_MEDIUM, SILVER,
                                 SCREEN_WIDTH//2 - trump_text.get_width()//2, 80)

        # Show whose turn it is to bet with animation
        current_player = self.game.players[self.game.current_player]
        turn_text = FONT_LARGE.render(f"{current_player.name}'s turn to bet", True, WHITE)
        self.draw_text_with_shadow(f"{current_player.name}'s turn to bet", FONT_LARGE, WHITE,
                                 SCREEN_WIDTH//2 - turn_text.get_width()//2, 130)
        
        # Show all players' bets so far with a nice background
        bet_info_y = 200  # Moved down to avoid overlap
        bet_box_height = len(self.game.players) * 40 + 20
        bet_bg = pygame.Surface((300, bet_box_height), pygame.SRCALPHA)
        bet_bg.fill((0, 0, 0, 128))
        self.screen.blit(bet_bg, (SCREEN_WIDTH//2 - 150, bet_info_y - 10))
        
        for i, player in enumerate(self.game.players):
            if player.bet is not None:
                bet_info = FONT_MEDIUM.render(f"{player.name} bet: {player.bet}", True, WHITE)
                self.draw_text_with_shadow(f"{player.name} bet: {player.bet}", FONT_MEDIUM, WHITE,
                                         SCREEN_WIDTH//2 - bet_info.get_width()//2, bet_info_y)
                bet_info_y += 40
        
        # Draw current player's hand with a nice background
        hand_y = SCREEN_HEIGHT - CARD_HEIGHT - 50
        x = (SCREEN_WIDTH - (len(current_player.hand) * (CARD_WIDTH + 10))) // 2
        
        # Draw a semi-transparent background for the hand
        hand_bg = pygame.Surface((len(current_player.hand) * (CARD_WIDTH + 10) + 20, CARD_HEIGHT + 20), pygame.SRCALPHA)
        hand_bg.fill((0, 0, 0, 128))
        self.screen.blit(hand_bg, (x - 10, hand_y - 10))
        
        for j, card in enumerate(current_player.hand):
            card.face_up = True
            self.draw_card(card, x + j * (CARD_WIDTH + 10), hand_y)
        
        # Bet display for current player
        selected_bet = getattr(self, 'selected_bet', None)
        bet_text = FONT_MEDIUM.render(
            f"Your bet: {selected_bet if selected_bet is not None else 'Not set'}", 
            True, WHITE)
        self.draw_text_with_shadow(f"Your bet: {selected_bet if selected_bet is not None else 'Not set'}", 
                                 FONT_MEDIUM, WHITE,
                                 SCREEN_WIDTH//2 - bet_text.get_width()//2, hand_y - 100)  # Moved up
        
        # Get valid bets for the current player
        valid_bets = self.game.get_valid_bets(self.game.current_player)
        
        # Bet buttons with nice styling
        button_y = hand_y - 160  # Moved up to avoid overlap
        button_width = 60
        button_height = 40
        button_spacing = 70
        
        center_x = SCREEN_WIDTH // 2
        start_x = center_x - (self.game.round * button_spacing) // 2
        
        self.bet_buttons = []
        for bet in range(0, self.game.round + 1):
            btn_x = start_x + bet * button_spacing
            btn_rect = pygame.Rect(btn_x, button_y, button_width, button_height)
            
            # Button styling
            if selected_bet == bet:
                btn_color = RED
                border_color = WHITE
            elif bet in valid_bets:
                btn_color = BLUE
                border_color = WHITE
            else:
                btn_color = GRAY
                border_color = BLACK
                
            self.draw_rounded_rect(self.screen, btn_color, btn_rect)
            pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=10)
            
            # Button label with shadow
            bet_label = FONT_MEDIUM.render(str(bet), True, WHITE)
            self.draw_text_with_shadow(str(bet), FONT_MEDIUM, WHITE,
                                     btn_x + button_width//2 - bet_label.get_width()//2,
                                     button_y + button_height//2 - bet_label.get_height()//2)
            
            self.bet_buttons.append((btn_rect, bet))
        
        # Submit button with nice styling
        submit_rect = pygame.Rect(center_x - 100, button_y - 60, 200, 50)
        submit_color = BLUE if selected_bet is not None else GRAY
        self.draw_rounded_rect(self.screen, submit_color, submit_rect)
        pygame.draw.rect(self.screen, WHITE, submit_rect, 2, border_radius=10)
        
        submit_text = "Submit Bet" if selected_bet is not None else "Place a bet first"
        submit_label = FONT_MEDIUM.render(submit_text, True, WHITE)
        self.draw_text_with_shadow(submit_text, FONT_MEDIUM, WHITE,
                                 center_x - submit_label.get_width()//2,
                                 button_y - 60 + 25 - submit_label.get_height()//2)
        
        self.submit_button = submit_rect
        pygame.display.flip()
        
    def draw_playing_screen(self):
        """Draw the main playing screen"""
        if self.showing_turn_screen:
            self.draw_turn_transition_screen()
            return

        self.screen.fill(GREEN)
        
        # Round and trump info
        round_text = FONT_MEDIUM.render(f"Round {self.game.round} | Trump: {SUITS[self.game.trump_suit].capitalize()}", True, WHITE)
        self.screen.blit(round_text, (20, 20))
        
        # Draw table cards
        if self.game.table:
            x = (SCREEN_WIDTH - (len(self.game.table) * (CARD_WIDTH + 10))) // 2
            y = SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2
            
            for i, card in enumerate(self.game.table):
                # Position cards in a circle around the center
                angle = (i * 2 * 3.14159) / self.game.n_players
                radius = 100
                card_x = x + radius * math.cos(angle)
                card_y = y + radius * math.sin(angle)
                self.draw_card(card, card_x, card_y)
                
        # Draw player info and current player's hand
        for i, player in enumerate(self.game.players):
            # Player info
            info_y = 0
            if i == 0:  # Bottom
                info_y = SCREEN_HEIGHT - 30
            elif i == 1:  # Left
                info_y = SCREEN_HEIGHT // 2
            elif i == 2:  # Top
                info_y = 30
            elif i == 3:  # Right
                info_y = SCREEN_HEIGHT // 2
                
            # Player info with bet and hands won
            info_text = FONT_SMALL.render(
                f"{player.name} | Score: {player.score} | Bet: {player.bet} | Won: {player.hands_won}", 
                True, WHITE)
            
            if i == 1 or i == 3:  # Left or right players
                # Rotate text vertically
                rotated_text = pygame.transform.rotate(info_text, 90 if i == 1 else -90)
                self.screen.blit(rotated_text, (30 if i == 1 else SCREEN_WIDTH - 50, info_y))
            else:
                self.screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, info_y))
            
            # Draw hand only for current player
            if i == self.game.current_player:
                hand_y = SCREEN_HEIGHT - CARD_HEIGHT - 50
                x = (SCREEN_WIDTH - (len(player.hand) * (CARD_WIDTH + 10))) // 2
                
                # Get valid moves
                playable_cards = self.game.get_valid_moves(self.game.current_player)
                
                for j, card in enumerate(player.hand):
                    highlight = j in playable_cards
                    self.draw_card(card, x + j * (CARD_WIDTH + 10), hand_y, highlight)
        
        # Current player indicator
        if self.game.state == "playing":
            current_player = self.game.players[self.game.current_player]
            indicator = FONT_MEDIUM.render(f"{current_player.name}'s turn", True, WHITE)
            self.screen.blit(indicator, (SCREEN_WIDTH//2 - indicator.get_width()//2, SCREEN_HEIGHT//2 + 100))
        
        pygame.display.flip()

    def draw_turn_transition_screen(self):
        """Draw the screen shown between player turns"""
        self.screen.fill(GREEN)
        
        current_player = self.game.players[self.game.current_player]
        
        # Show who's turn is next
        text1 = FONT_LARGE.render(f"{current_player.name}'s Turn", True, WHITE)
        text2 = FONT_MEDIUM.render("Click anywhere to continue", True, WHITE)
        
        self.screen.blit(text1, (SCREEN_WIDTH//2 - text1.get_width()//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(text2, (SCREEN_WIDTH//2 - text2.get_width()//2, SCREEN_HEIGHT//2 + 50))
        
        pygame.display.flip()

    def handle_setup_events(self, event):
        logger.debug("Handling setup events")
        if event.type == KEYDOWN:
            if event.key == K_RETURN:
                names = [name.strip() for name in self.name_input.split(",") if name.strip()]
                if len(names) >= 2 and len(names) <= 4:
                    logger.info(f"Starting game with players: {names}")
                    self.player_names = names
                    self.game = Game(self.player_names)
                    self.game.initialize_round(1)
                    # Set initial player's cards face up
                    self.update_card_visibility()
            elif event.key == K_BACKSPACE:
                self.name_input = self.name_input[:-1]
            else:
                self.name_input += event.unicode
                
        elif event.type == MOUSEBUTTONDOWN:
            # Check if start button was clicked
            mouse_pos = pygame.mouse.get_pos()
            if (SCREEN_WIDTH//2 - 100 <= mouse_pos[0] <= SCREEN_WIDTH//2 + 100 and
                300 <= mouse_pos[1] <= 350):
                names = [name.strip() for name in self.name_input.split(",") if name.strip()]
                if len(names) >= 2 and len(names) <= 4:
                    logger.info(f"Starting game with players: {names}")
                    self.player_names = names
                    self.game = Game(self.player_names)
                    self.game.initialize_round(1)
                    # Set initial player's cards face up
                    self.update_card_visibility()

    def update_card_visibility(self):
        """Update card visibility for the current player"""
        logger.info(f"Updating card visibility for player {self.game.current_player}")
        # Set current player's cards face up
        current_player = self.game.players[self.game.current_player]
        for card in current_player.hand:
            card.face_up = True

    def handle_betting_events(self, event):
        logger.debug("Handling betting events")
        if event.type == MOUSEBUTTONDOWN and event.button == 1:  # Left mouse click
            mouse_pos = pygame.mouse.get_pos()
            current_player = self.game.players[self.game.current_player]
            
            # Check bet buttons
            if hasattr(self, 'bet_buttons'):
                for btn_rect, bet in self.bet_buttons:
                    if btn_rect.collidepoint(mouse_pos):
                        # Only allow valid bets
                        valid_bets = self.game.get_valid_bets(self.game.current_player)
                        if bet in valid_bets:
                            logger.info(f"{current_player.name} selected bet: {bet}")
                            # Only store the selected bet, don't set it yet
                            self.selected_bet = bet
                        return  # Exit after handling
            
            # Check submit button
            if hasattr(self, 'submit_button') and hasattr(self, 'selected_bet'):
                if self.submit_button.collidepoint(mouse_pos):
                    logger.info(f"{current_player.name} submitted bet: {self.selected_bet}")
                    # Set the bet and mark player as submitted
                    current_player.bet = self.selected_bet
                    self.game.bets[self.game.current_player] = self.selected_bet
                    self.submitted_bets.append(self.game.current_player)
                    
                    # Move to next player
                    next_player_index = (self.game.current_player + 1) % self.game.n_players
                    self.game.current_player = next_player_index
                    
                    # Reset selected bet for next player
                    self.selected_bet = None
                    
                    # Check if all players have submitted their bets
                    if len(self.submitted_bets) == self.game.n_players:
                        logger.info("All players have submitted their bets, starting play phase")
                        self.game.state = "playing"
                        self.game.current_player = 0  # First player starts
                        self.showing_turn_screen = True
                        self.submitted_bets = []  # Reset for next round
                    else:
                        # Update card visibility for next player
                        self.update_card_visibility()
                    return

    def place_ai_bets(self):
        # Remove AI betting logic since we're using human players only
        self.game.state = "playing"
        logger.info("All bets placed, starting play phase")

    def handle_playing_events(self, event):
        logger.debug("Handling playing events")
        
        if self.showing_turn_screen:
            if event.type == MOUSEBUTTONDOWN:
                self.showing_turn_screen = False
            return
            
        if event.type == MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if a card was clicked
            player = self.game.players[self.game.current_player]
            x_start = (SCREEN_WIDTH - (len(player.hand) * (CARD_WIDTH + 10))) // 2
            y_pos = SCREEN_HEIGHT - CARD_HEIGHT - 50
            
            for i in range(len(player.hand)):
                card_x = x_start + i * (CARD_WIDTH + 10)
                if (card_x <= mouse_pos[0] <= card_x + CARD_WIDTH and
                    y_pos <= mouse_pos[1] <= y_pos + CARD_HEIGHT):
                    logger.info(f"Player attempting to play card {i}")
                    if self.game.play_card(self.game.current_player, i):
                        self.selected_card = None
                        # Show turn transition screen for next player
                        self.showing_turn_screen = True
                    else:
                        self.selected_card = i

    def calculate_round_scores(self):
        """Calculate scores for the round once"""
        for player in self.game.players:
            # Calculate points for this round
            points = 10 if player.hands_won == player.bet else 0
            logger.info(f"{player.name}: Bet {player.bet}, Won {player.hands_won}, Points {points}, Total Score {player.score}")

    def draw_round_over_screen(self):
        """Draw the round over screen with total scores"""
        self.screen.fill(GREEN)
        
        # Title
        title = FONT_LARGE.render(f"Round {self.game.round} Over", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Show scores
        y = 150
        for player in self.game.players:
            # Show player's total score
            score_text = FONT_LARGE.render(f"{player.name}: {player.score}", True, WHITE)
            self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, y))
            y += 60
            
        # Next round button
        button_y = y + 20
        pygame.draw.rect(self.screen, BLUE, (SCREEN_WIDTH//2 - 100, button_y, 200, 50))
        next_text = FONT_MEDIUM.render("Next Round", True, WHITE)
        self.screen.blit(next_text, (SCREEN_WIDTH//2 - next_text.get_width()//2, button_y + 10))
        
        pygame.display.flip()

    def handle_round_over_events(self, event):
        logger.debug("Handling round over events")
        if event.type == MOUSEBUTTONDOWN and event.button == 1:  # Left mouse click
            mouse_pos = pygame.mouse.get_pos()
            
            # Calculate button position the same way as in draw_round_over_screen
            y = 150  # Starting y position for scores
            y += len(self.game.players) * 60  # Account for player scores (60 pixels per player)
            button_y = y + 20  # Add spacing for button
            
            # Check if next round button was clicked
            if (SCREEN_WIDTH//2 - 100 <= mouse_pos[0] <= SCREEN_WIDTH//2 + 100 and
                button_y <= mouse_pos[1] <= button_y + 50):
                
                # Reset scores calculated flag
                if hasattr(self, '_scores_calculated'):
                    delattr(self, '_scores_calculated')
                
                # Check if there are more rounds to play
                if not self.game.is_game_over():
                    logger.info("Starting next round")
                    self.game.initialize_round(self.game.round + 1)
                    self.game.state = "betting"  # Make sure we go back to betting state
                    self.game.current_player = 0  # Reset to first player
                    self.submitted_bets = []  # Reset submitted bets list
                else:
                    logger.info("Game over - showing final scores")
                    self.show_final_scores()

    def show_final_scores(self):
        logger.info("Showing final scores")
        self.screen.fill(GREEN)
        
        # Game over title
        title = FONT_LARGE.render("Game Over - Final Scores", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Show final scores
        y = 120
        for player in sorted(self.game.players, key=lambda p: p.score, reverse=True):
            score_text = FONT_MEDIUM.render(
                f"{player.name}: {player.score} points", True, WHITE)
            self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, y))
            y += 40
            logger.info(f"Final score - {player.name}: {player.score} points")
        
        # Play again button
        pygame.draw.rect(self.screen, BLUE, (SCREEN_WIDTH//2 - 100, y + 50, 200, 50))
        again_text = FONT_MEDIUM.render("Play Again", True, WHITE)
        self.screen.blit(again_text, (SCREEN_WIDTH//2 - again_text.get_width()//2, y + 65))
        
        pygame.display.flip()
        
        # Wait for play again click
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == QUIT:
                    logger.info("Game quit by user")
                    pygame.quit()
                    sys.exit()
                elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if (SCREEN_WIDTH//2 - 100 <= mouse_pos[0] <= SCREEN_WIDTH//2 + 100 and
                        y + 50 <= mouse_pos[1] <= y + 100):
                        logger.info("Starting new game")
                        waiting = False
                        self.__init__()  # Reset the game

    def run(self):
        logger.info("Starting game loop")
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    logger.info("Game quit by user")
                    running = False
                
                # Handle game state transitions
                if not self.game:
                    self.handle_setup_events(event)
                elif self.game.state == "betting":
                    self.handle_betting_events(event)
                elif self.game.state == "playing":
                    self.handle_playing_events(event)
                elif self.game.state == "round_over":
                    # Calculate scores once when entering round_over state
                    if not hasattr(self, '_scores_calculated'):
                        self.calculate_round_scores()
                        self._scores_calculated = True
                    self.handle_round_over_events(event)
            
            # Draw the appropriate screen
            if not self.game:
                self.draw_setup_screen()
            elif self.game.state == "betting":
                self.draw_betting_screen()
            elif self.game.state == "playing":
                self.draw_playing_screen()
            elif self.game.state == "round_over":
                self.draw_round_over_screen()
            
            self.clock.tick(30)

if __name__ == "__main__":
    logger.info("Starting Kachuful game")
    game = KachufulGame()
    game.run() 