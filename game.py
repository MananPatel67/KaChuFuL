import random 


class Card:
    def __init__(self, card):
        self.card = card

        self.mapping = "2,3,4,5,6,7,8,9".split(',') + ["10" , "J", "Q", "K", "A"]

    def __str__(self):
        return f'{self.mapping[self.card % 13]}{"♠♦♣♥"[self.card // 13]}'


class Deck:
    def __init__(self):
        self.deck = [Card(i) for i in range(52)]
    
    def shuffle(self):
        random.shuffle(self.deck)

    def draw(self, number):
        return [self.deck.pop() for _ in range(number)]
    
    def __getitem__(self, key):
        return self.deck[key]


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0
        self.hands_won = 0
    
    def add_to_hand(self, *cards):
        [self.hand.append(card) for card in cards]
    
    def play_hand(self , number):
        return self.hand.pop(number)
    
    def __str__(self):
        return self.name

class Game:
    def __init__(self, player_names):
        self.round = 0
        self.n_players = len(player_names)
        self.player_names = player_names
        self.players = [Player(name) for name in player_names]
        self.current_player = 0
        self.table = []
        self.evaluations = []
        self.trump_card = -1

    def initalize_round(self, round):
        assert round * self.n_players <= 52, "Wrong"
        self.players = [Player(self.player_names[i%self.n_players]) for i in range(round-1,round+self.n_players-1)]
        self.round = round
        deck = Deck()
        deck.shuffle()
        [player.add_to_hand(*deck.draw(round)) for player in self.players]
        self.current_player = 0
        self.trump_card = (self.trump_card + 1) % 4

    def place_bets(self, bets: list):
        self.bets = bets

    def play_hand(self, number):
        card_played = self.players[self.current_player].play_hand(number)
        self.evaluations.append(((card_played.card % 13) + 26) if (card_played.card // 13 == self.trump_card) else ((card_played.card % 13) + 13) if len(self.table) == 0 or (self.table[0].card // 13 == card_played.card // 13) else 0)
        self.table.append(card_played)
        self.current_player = (self.current_player + 1) % self.n_players
        
    def evaluate_table(self):
        player_won = self.evaluations.index(max(self.evaluations))
        self.players[player_won].hands_won += 1
        self.evaluations = []
        self.table = []
        self.players = self.players[player_won:] + self.players[:player_won]
        self.bets = self.bets[player_won:] + self.bets[:player_won]

    def close_round(self):
        for player, bet in zip(self.players, self.bets):
            player.score += (10 if player.hands_won == bet else -10) * max(bet, 1)
            print(f'increment of {player}:{(10 if player.hands_won == bet else -10) * max(bet, 1)}')
            print(f'{player} won {player.hands_won} hands on the bet of {bet}')
            player.hands_won = 0


if __name__ == "__main__":
    player_names = input("Enter name of players: ").split()
    n_players = len(player_names)
    game = Game(player_names)
    for round in range(1, (52 // n_players) + 1):
        print(f"Round {round}")
        game.initalize_round(round)
        print(f'Trump suit: {"♠♦♣♥"[game.trump_card]}')
        game.place_bets([int(input(f"Cards in hand for {player}:" + " ".join([str(card) for card in player.hand]) + f'\nEnter bet for {player}: ')) for player in game.players])
        for _ in range(round):
            for player in game.players:
                print("Cards on the table: ", [str(card) for card in game.table])
                print(f"Cards in hand for {player}:", {i: str(card) for i, card in enumerate(player.hand)})
                game.play_hand(int(input(f"Enter card to play for {player}: ")))
            game.evaluate_table()
        game.close_round()
        print("Scores:", {str(player): player.score for player in game.players})
