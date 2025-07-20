import tkinter as tk
from tkinter import messagebox, ttk
import random
from typing import List, Tuple
import os

class Card:
    """Represents a playing card with suit and value."""
    
    def __init__(self, suit: str, value: str):
        self.suit = suit
        self.value = value
        
    def __str__(self):
        return f"{self.value} of {self.suit}"
    
    def get_value(self) -> int:
        """Get the numerical value of the card for blackjack scoring."""
        if self.value in ['J', 'Q', 'K']:
            return 10
        elif self.value == 'A':
            return 11  # Ace will be handled specially in hand calculation
        else:
            return int(self.value)

class Deck:
    """Represents a deck of 52 playing cards."""
    
    def __init__(self):
        self.cards = []
        self.original_size = 52
        self.reset()
    
    def reset(self):
        """Reset the deck to a fresh 52-card deck."""
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        self.cards = [Card(suit, value) for suit in suits for value in values]
        self.shuffle()
    
    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)
    
    def deal(self) -> Card:
        """Deal one card from the deck."""
        if not self.cards:
            self.reset()
        return self.cards.pop()
    
    def get_remaining_percentage(self) -> float:
        """Get the percentage of cards remaining in the deck."""
        return (len(self.cards) / self.original_size) * 100

    def get_remaining_cards(self) -> float:
        """Get the number of cards remaining in the deck."""
        return len(self.cards)
    
    def should_shuffle(self) -> bool:
        """Check if deck should be shuffled (when 50% or fewer cards remain)."""
        return len(self.cards) <= self.original_size // 2

class Hand:
    """Represents a hand of cards (player or dealer)."""
    
    def __init__(self):
        self.cards = []
        self.bet_size = 0
    
    def add_card(self, card: Card):
        """Add a card to the hand."""
        self.cards.append(card)
    
    def get_value(self) -> int:
        """Calculate the total value of the hand."""
        value = 0
        aces = 0
        
        for card in self.cards:
            if card.value == 'A':
                aces += 1
            else:
                value += card.get_value()
        
        # Add aces
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
        
        return value
    
    def is_bust(self) -> bool:
        """Check if the hand is bust (over 21)."""
        return self.get_value() > 21
    
    def is_blackjack(self) -> bool:
        """Check if the hand is a blackjack (Ace + 10-value card)."""
        #TODO: Check if the hand was split. If so, do not count it as a blackjack.
        return len(self.cards) == 2 and self.get_value() == 21
    
    def clear(self):
        """Clear all cards from the hand."""
        self.cards = []
        self.bet_size = 0
    
    def set_bet(self, amount: int):
        """Set the bet size for this hand."""
        self.bet_size = amount

class Player:
    """Represents a player with multiple hands."""
    
    def __init__(self):
        self.hands = []
        self.current_hand_index = 0
    
    def add_hand(self, hand: Hand):
        """Add a hand to the player."""
        self.hands.append(hand)
    
    def get_current_hand(self) -> Hand | None:
        """Get the current hand being played."""
        if self.hands:
            return self.hands[self.current_hand_index]
        return None
    
    def next_hand(self) -> bool:
        """Move to the next hand. Returns True if there are more hands."""
        if self.current_hand_index < len(self.hands) - 1:
            self.current_hand_index += 1
            return True
        return False
    
    def clear_hands(self):
        """Clear all hands."""
        self.hands = []
        self.current_hand_index = 0

class Dealer:
    """Represents a dealer with a hand and playing strategy."""
    
    def __init__(self):
        self.hand = Hand()
    
    def add_card(self, card: Card):
        """Add a card to the dealer's hand."""
        self.hand.add_card(card)
    
    def get_hand(self) -> Hand:
        """Get the dealer's hand."""
        return self.hand
    
    def play_hand(self, deck: Deck):
        """Play the dealer's hand according to standard rules (hit on 16, stand on 17)."""
        while self.hand.get_value() < 17:
            self.hand.add_card(deck.deal())
    
    def clear_hand(self):
        """Clear the dealer's hand."""
        self.hand.clear()

class BlackjackGame:
    """Main blackjack game logic."""
    
    def __init__(self):
        self.deck = Deck()
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.game_over = False
        self.player_wins = 0
        self.dealer_wins = 0
        self.ties = 0
        self.can_double = False
        self.can_split = False
        self.split_hands = []
        self.current_hand_index = 0
        self.is_split_game = False
        self.bet_size = 0  # Track the bet size for the current hand
        self.total_winnings = 0  # Track total winnings
        self.doubled = False  # Track if current hand was doubled
    
    def set_bet(self, amount: int) -> bool:
        """Set the bet size for the current hand."""
        if amount <= 0:
            return False
        self.bet_size = amount
        return True
    
    def get_payout(self) -> int:
        """Calculate payout based on game result and bet size."""
        if self.bet_size == 0:
            return 0
        
        if self.is_split_game:
            # Handle split game payouts
            dealer_value = self.dealer_hand.get_value()
            total_payout = 0
            
            # Each split hand has its own bet (same as original bet)
            split_bet = self.bet_size
            
            for hand in self.split_hands:
                player_value = hand.get_value()
                
                if hand.is_bust():
                    # Lose bet for this hand
                    total_payout -= split_bet
                elif self.dealer_hand.is_bust():
                    # Win bet for this hand
                    total_payout += split_bet
                elif hand.get_value() == 21 and not self.dealer_hand.is_blackjack():
                    # Regular 21 on split hand (not blackjack)
                    total_payout += split_bet
                elif self.dealer_hand.is_blackjack() and not hand.is_blackjack():
                    # Lose bet for this hand
                    total_payout -= split_bet
                elif player_value > dealer_value:
                    # Win bet for this hand
                    total_payout += split_bet
                elif dealer_value > player_value:
                    # Lose bet for this hand
                    total_payout -= split_bet
                else:
                    # Push (tie) - return original bet (no change to payout)
                    pass
            
            return total_payout
        else:
            # Handle regular game payout
            player_value = self.player_hand.get_value()
            dealer_value = self.dealer_hand.get_value()
            
            # Calculate payout multiplier (2x for doubled hands)
            payout_multiplier = 2 if self.doubled else 1
            
            if self.player_hand.is_bust():
                return -1*self.bet_size * payout_multiplier  # Lose bet
            elif self.dealer_hand.is_bust():
                return self.bet_size * payout_multiplier  # Win bet
            elif self.player_hand.is_blackjack() and not self.dealer_hand.is_blackjack():
                return int(self.bet_size * 1.5 * payout_multiplier)  # Blackjack pays 3:2
            elif self.dealer_hand.is_blackjack() and not self.player_hand.is_blackjack():
                return -1*self.bet_size * payout_multiplier  # Lose bet
            elif player_value > dealer_value:
                return self.bet_size * payout_multiplier  # Win bet
            elif dealer_value > player_value:
                return -1*self.bet_size * payout_multiplier  # Lose bet
            else:
                return 0  # Push (tie) - return original bet
    
    def update_money_tracking(self):
        """Update total winnings and losses based on current game result."""
        if self.bet_size == 0:
            return
        
        payout = self.get_payout()
        self.total_winnings += payout 
    
    def log_game_result(self):
        """Log the final game state to terminal."""
        
        # Log dealer's final hand
        dealer_cards = [str(card) for card in self.dealer_hand.cards]
        dealer_value = self.dealer_hand.get_value()
        print(f"Dealer's Final Hand: {', '.join(dealer_cards)} (Value: {dealer_value})")
        
        # Log player's final hand(s)
        if self.is_split_game:
            print("Player's Final Hands:")
            for i, hand in enumerate(self.split_hands):
                cards = [str(card) for card in hand.cards]
                value = hand.get_value()
                print(f"  Hand {i+1}: {', '.join(cards)} (Value: {value})")
        else:
            player_cards = [str(card) for card in self.player_hand.cards]
            player_value = self.player_hand.get_value()
            print(f"Player's Final Hand: {', '.join(player_cards)} (Value: {player_value})")
        
        # Log bet and payout
        payout = self.get_payout()
        print(f"Bet Amount: ${self.bet_size}")
        print(f"Payout: ${payout}")
        
        # Log game result
        if self.is_split_game:
            dealer_value = self.dealer_hand.get_value()
            results = []
            for i, hand in enumerate(self.split_hands):
                player_value = hand.get_value()
                if hand.is_bust():
                    results.append(f"Hand {i+1}: BUST")
                elif self.dealer_hand.is_bust():
                    results.append(f"Hand {i+1}: WIN")
                elif hand.get_value() == 21 and not self.dealer_hand.is_blackjack():
                    results.append(f"Hand {i+1}: WIN")
                elif self.dealer_hand.is_blackjack() and not hand.is_blackjack():
                    results.append(f"Hand {i+1}: LOSE")
                elif player_value > dealer_value:
                    results.append(f"Hand {i+1}: WIN")
                elif dealer_value > player_value:
                    results.append(f"Hand {i+1}: LOSE")
                else:
                    results.append(f"Hand {i+1}: TIE")
            print(f"Result: {' | '.join(results)}")
        else:
            player_value = self.player_hand.get_value()
            dealer_value = self.dealer_hand.get_value()
            
            if self.player_hand.is_bust():
                result = "BUST - Player loses"
            elif self.dealer_hand.is_bust():
                result = "Dealer busts - Player wins"
            elif self.player_hand.is_blackjack() and not self.dealer_hand.is_blackjack():
                result = "BLACKJACK - Player wins"
            elif self.dealer_hand.is_blackjack() and not self.player_hand.is_blackjack():
                result = "Dealer blackjack - Player loses"
            elif player_value > dealer_value:
                result = "Player wins"
            elif dealer_value > player_value:
                result = "Dealer wins"
            else:
                result = "TIE"
            print(f"Result: {result}")
        
        print(f"Total Winnings: ${self.total_winnings}")
        print("="*50)
    
    def start_new_game(self):
        """Start a new game."""
        shuffle_notification = ""
        if self.deck.should_shuffle():
            self.deck.reset()
            shuffle_notification = "Deck shuffled!"
        
        self.player_hand.clear()
        self.dealer_hand.clear()
        self.game_over = False
        self.can_double = False
        self.can_split = False
        self.split_hands = []
        self.current_hand_index = 0
        self.is_split_game = False
        self.bet_size = 0  # Require new bet before dealing
        self.doubled = False  # Reset doubled flag
        # Do NOT deal cards yet
        return shuffle_notification

    def deal_initial_cards(self):
        """Deal the initial cards after a bet is placed."""
        self.player_hand.clear()
        self.dealer_hand.clear()
        self.split_hands = []
        self.current_hand_index = 0
        self.is_split_game = False
        self.game_over = False
        self.can_double = False
        self.can_split = False
        self.doubled = False  # Reset doubled flag
        # Deal initial cards
        self.player_hand.add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        self.player_hand.add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        
        # Check for immediate blackjack
        if self.player_hand.is_blackjack() or self.dealer_hand.is_blackjack():
            self.end_game()
            return
        
        # Check if double is possible (only on first two cards)
        if len(self.player_hand.cards) == 2:
            self.can_double = True
        # Check if split is possible (same value cards)
        if (len(self.player_hand.cards) == 2 and 
            self.player_hand.cards[0].get_value() == self.player_hand.cards[1].get_value()):
            self.can_split = True

    def hit(self):
        """Player hits (takes another card)."""
        if not self.game_over:
            current_hand = self.get_current_hand()
            current_hand.add_card(self.deck.deal())
            
            # Disable double after first hit
            self.can_double = False
            
            if current_hand.is_bust():
                if self.is_split_game and self.current_hand_index < len(self.split_hands) - 1:
                    # Move to next split hand
                    self.current_hand_index += 1
                else:
                    self.end_game()
    
    def double(self):
        """Player doubles (hit once and stand)."""
        if not self.game_over and self.can_double:
            current_hand = self.get_current_hand()
            current_hand.add_card(self.deck.deal())
            self.can_double = False
            self.doubled = True  # Mark that this hand was doubled
            
            if current_hand.is_bust():
                if self.is_split_game and self.current_hand_index < len(self.split_hands) - 1:
                    self.current_hand_index += 1
                else:
                    self.end_game()
            else:
                # After double, automatically stand
                if self.is_split_game and self.current_hand_index < len(self.split_hands) - 1:
                    self.current_hand_index += 1
                else:
                    self.stand()
    
    def split(self):
        """Player splits the hand."""
        if not self.game_over and self.can_split and len(self.player_hand.cards) == 2:
            # Create two new hands from the split
            card1 = self.player_hand.cards[0]
            card2 = self.player_hand.cards[1]
            
            # Create split hands
            hand1 = Hand()
            hand1.add_card(card1)
            hand1.add_card(self.deck.deal())
            
            hand2 = Hand()
            hand2.add_card(card2)
            hand2.add_card(self.deck.deal())
            
            self.split_hands = [hand1, hand2]
            self.is_split_game = True
            self.current_hand_index = 0
            self.can_split = False
            self.can_double = True  # Can double on split hands
    
    def get_current_hand(self):
        """Get the current hand being played."""
        if self.is_split_game and self.split_hands:
            return self.split_hands[self.current_hand_index]
        return self.player_hand
    
    def stand(self):
        """Player stands (dealer plays)."""
        if not self.game_over:
            if self.is_split_game and self.current_hand_index < len(self.split_hands) - 1:
                # Move to next split hand
                self.current_hand_index += 1
                self.can_double = True  # Can double on next split hand
            else:
                self.dealer_play()
                self.end_game()
    
    def dealer_play(self):
        """Dealer plays according to standard rules (hit on 16, stand on 17)."""
        while self.dealer_hand.get_value() < 17:
            self.dealer_hand.add_card(self.deck.deal())
    
    def end_game(self):
        """End the game and determine the winner."""
        self.game_over = True
        
        # Update money tracking
        self.update_money_tracking()
        
        # Log the final game state
        self.log_game_result()
        
        if self.is_split_game:
            # Handle split game results
            dealer_value = self.dealer_hand.get_value()
            player_wins_this_round = 0
            dealer_wins_this_round = 0
            ties_this_round = 0
            
            for hand in self.split_hands:
                player_value = hand.get_value()
                
                if hand.is_bust():
                    dealer_wins_this_round += 1
                elif self.dealer_hand.is_bust():
                    player_wins_this_round += 1
                elif hand.is_blackjack() and not self.dealer_hand.is_blackjack():
                    player_wins_this_round += 1
                elif self.dealer_hand.is_blackjack() and not hand.is_blackjack():
                    dealer_wins_this_round += 1
                elif player_value > dealer_value:
                    player_wins_this_round += 1
                elif dealer_value > player_value:
                    dealer_wins_this_round += 1
                else:
                    ties_this_round += 1
            
            self.player_wins += player_wins_this_round
            self.dealer_wins += dealer_wins_this_round
            self.ties += ties_this_round
        else:
            # Handle regular game
            player_value = self.player_hand.get_value()
            dealer_value = self.dealer_hand.get_value()
            
            if self.player_hand.is_bust():
                self.dealer_wins += 1
            elif self.dealer_hand.is_bust():
                self.player_wins += 1
            elif self.player_hand.is_blackjack() and not self.dealer_hand.is_blackjack():
                self.player_wins += 1
            elif self.dealer_hand.is_blackjack() and not self.player_hand.is_blackjack():
                self.dealer_wins += 1
            elif player_value > dealer_value:
                self.player_wins += 1
            elif dealer_value > player_value:
                self.dealer_wins += 1
            else:
                self.ties += 1

class BlackjackGUI:
    """Graphical user interface for the blackjack game."""
    
    def __init__(self):
        self.game = BlackjackGame()
        self.root = tk.Tk()
        self.root.title("Blackjack")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c5530')  # Dark green background
        
        self.setup_ui()
        self.start_new_game()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Set up ttk styles
        style = ttk.Style()
        style.theme_use('clam')  # Use clam theme for better cross-platform consistency
        
        # Create custom button styles with colors
        style.configure('Hit.TButton', background='#00C851', foreground='white')
        style.map('Hit.TButton', 
                 background=[('active', '#00A041'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        style.configure('Stand.TButton', background='#FF4444', foreground='white')
        style.map('Stand.TButton', 
                 background=[('active', '#CC3333'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        style.configure('Double.TButton', background='#FF6B35', foreground='white')
        style.map('Double.TButton', 
                 background=[('active', '#E55A2B'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        style.configure('Split.TButton', background='#9932CC', foreground='white')
        style.map('Split.TButton', 
                 background=[('active', '#7A28A3'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        style.configure('NewGame.TButton', background='#4285F4', foreground='white')
        style.map('NewGame.TButton', 
                 background=[('active', '#3367D6'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        # Title
        title_label = tk.Label(
            self.root, 
            text="BLACKJACK", 
            font=("Arial", 24, "bold"), 
            fg='white', 
            bg='#2c5530'
        )
        title_label.pack(pady=10)
        
        # Stats frame
        stats_frame = tk.Frame(self.root, bg='#2c5530')
        stats_frame.pack(pady=5)
        
        self.player_score_label = tk.Label(
            stats_frame, 
            text="Player: 0", 
            font=("Arial", 12), 
            fg='white', 
            bg='#2c5530'
        )
        self.player_score_label.pack(side=tk.LEFT, padx=10)
        
        self.dealer_score_label = tk.Label(
            stats_frame, 
            text="Dealer: 0", 
            font=("Arial", 12), 
            fg='white', 
            bg='#2c5530'
        )
        self.dealer_score_label.pack(side=tk.LEFT, padx=10)
        
        self.ties_label = tk.Label(
            stats_frame, 
            text="Ties: 0", 
            font=("Arial", 12), 
            fg='white', 
            bg='#2c5530'
        )
        self.ties_label.pack(side=tk.LEFT, padx=10)
        
        self.deck_status_label = tk.Label(
            stats_frame, 
            text="Deck: 100%", 
            font=("Arial", 12), 
            fg='white', 
            bg='#2c5530'
        )
        self.deck_status_label.pack(side=tk.LEFT, padx=10)
        
        # Winnings/Losses frame
        money_frame = tk.Frame(self.root, bg='#2c5530')
        money_frame.pack(pady=5)
        
        self.winnings_label = tk.Label(
            money_frame, 
            text="Winnings: $0", 
            font=("Arial", 14, "bold"), 
            fg='#00FF00', 
            bg='#2c5530'
        )
        self.winnings_label.pack(side=tk.LEFT, padx=10)
        
        # Dealer section
        dealer_frame = tk.Frame(self.root, bg='#2c5530')
        dealer_frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Label(
            dealer_frame, 
            text="DEALER", 
            font=("Arial", 16, "bold"), 
            fg='white', 
            bg='#2c5530'
        ).pack()
        
        self.dealer_hand_label = tk.Label(
            dealer_frame, 
            text="", 
            font=("Arial", 12), 
            fg='white', 
            bg='#2c5530',
            wraplength=700
        )
        self.dealer_hand_label.pack()
        
        self.dealer_value_label = tk.Label(
            dealer_frame, 
            text="", 
            font=("Arial", 12), 
            fg='white', 
            bg='#2c5530'
        )
        self.dealer_value_label.pack()
        
        # Player section
        player_frame = tk.Frame(self.root, bg='#2c5530')
        player_frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Label(
            player_frame, 
            text="PLAYER", 
            font=("Arial", 16, "bold"), 
            fg='white', 
            bg='#2c5530'
        ).pack()
        
        self.player_hand_label = tk.Label(
            player_frame, 
            text="", 
            font=("Arial", 12), 
            fg='white', 
            bg='#2c5530',
            wraplength=700
        )
        self.player_hand_label.pack()
        
        self.player_value_label = tk.Label(
            player_frame, 
            text="", 
            font=("Arial", 12), 
            fg='white', 
            bg='#2c5530'
        )
        self.player_value_label.pack()
        
        # Betting frame
        betting_frame = tk.Frame(self.root, bg='#2c5530')
        betting_frame.pack(pady=10)
        
        tk.Label(
            betting_frame,
            text="Bet Amount:",
            font=("Arial", 12),
            fg='white',
            bg='#2c5530'
        ).pack(side=tk.LEFT, padx=5)
        
        self.bet_entry = tk.Entry(
            betting_frame,
            font=("Arial", 12),
            width=10
        )
        self.bet_entry.pack(side=tk.LEFT, padx=5)
        self.bet_entry.insert(0, "10")
        
        self.place_bet_button = tk.Button(
            betting_frame,
            text="PLACE BET",
            command=self.place_bet,
            font=("Arial", 12, "bold"),
            bg='#FFD700',
            fg='black',
            relief=tk.RAISED,
            bd=2
        )
        self.place_bet_button.pack(side=tk.LEFT, padx=10)
        
        # Buttons frame
        buttons_frame = tk.Frame(self.root, bg='#2c5530')
        buttons_frame.pack(pady=20)
        
        self.hit_button = ttk.Button(
            buttons_frame, 
            text="HIT", 
            command=self.hit,
            style="Hit.TButton",
            width=10
        )
        self.hit_button.pack(side=tk.LEFT, padx=10)
        
        self.stand_button = ttk.Button(
            buttons_frame, 
            text="STAND", 
            command=self.stand,
            style="Stand.TButton",
            width=10
        )
        self.stand_button.pack(side=tk.LEFT, padx=10)
        
        self.double_button = ttk.Button(
            buttons_frame, 
            text="DOUBLE", 
            command=self.double,
            style="Double.TButton",
            width=10
        )
        self.double_button.pack(side=tk.LEFT, padx=10)
        
        self.split_button = ttk.Button(
            buttons_frame, 
            text="SPLIT", 
            command=self.split,
            style="Split.TButton",
            width=10
        )
        self.split_button.pack(side=tk.LEFT, padx=10)
        
        # Status label
        self.status_label = tk.Label(
            self.root, 
            text="", 
            font=("Arial", 14, "bold"), 
            fg='yellow', 
            bg='#2c5530'
        )
        self.status_label.pack(pady=10)
    
    def update_display(self):
        """Update the display with current game state."""
        # Update dealer hand
        if self.game.bet_size == 0 or len(self.game.dealer_hand.cards) == 0:
            dealer_text = "Cards: No cards dealt yet"
            dealer_value = 0
        elif self.game.game_over:
            dealer_cards = [str(card) for card in self.game.dealer_hand.cards]
            dealer_text = f"Cards: {', '.join(dealer_cards)}"
            dealer_value = self.game.dealer_hand.get_value()
        else:
            # Hide dealer's first card
            dealer_cards = [str(self.game.dealer_hand.cards[0]), "Hidden"]
            dealer_text = f"Cards: {', '.join(dealer_cards)}"
            dealer_value = self.game.dealer_hand.cards[0].get_value()
        self.dealer_hand_label.config(text=dealer_text)
        self.dealer_value_label.config(text=f"Value: {dealer_value}")
        # Update player hand(s)
        if self.game.bet_size == 0 or len(self.game.player_hand.cards) == 0:
            player_text = "Cards: No cards dealt yet"
            player_value = 0
        elif self.game.is_split_game and self.game.split_hands:
            split_text = ""
            for i, hand in enumerate(self.game.split_hands):
                cards = [str(card) for card in hand.cards]
                hand_text = f"Hand {i+1}: {', '.join(cards)} (Value: {hand.get_value()})"
                if i == self.game.current_hand_index and not self.game.game_over:
                    hand_text += " ← Current"
                split_text += hand_text + "\n"
            self.player_hand_label.config(text=split_text.rstrip())
            self.player_value_label.config(text=f"Split Game - Hand {self.game.current_hand_index + 1}")
        else:
            player_cards = [str(card) for card in self.game.player_hand.cards]
            player_text = f"Cards: {', '.join(player_cards)}"
            player_value = self.game.player_hand.get_value()
            self.player_hand_label.config(text=player_text)
            self.player_value_label.config(text=f"Value: {player_value}")
        # Update stats
        self.player_score_label.config(text=f"Player: {self.game.player_wins}")
        self.dealer_score_label.config(text=f"Dealer: {self.game.dealer_wins}")
        self.ties_label.config(text=f"Ties: {self.game.ties}")
        self.deck_status_label.config(text=f"Deck: {self.game.deck.get_remaining_cards()}")
        # Update winnings/losses display with color coding
        winnings_text = f"Winnings: ${self.game.total_winnings}"
        if self.game.total_winnings > 0:
            self.winnings_label.config(text=winnings_text, fg='#00FF00')  # Green for positive
        elif self.game.total_winnings < 0:
            self.winnings_label.config(text=winnings_text, fg='#FF0000')  # Red for negative
        else:
            self.winnings_label.config(text=winnings_text, fg='#FFFFFF')  # White for zero
        # Update bet info
        if self.game.bet_size > 0:
            self.status_label.config(text=f"Current Bet: ${self.game.bet_size}", fg='yellow')
        # Update button states
        if self.game.bet_size == 0 or len(self.game.player_hand.cards) == 0 or self.game.game_over:
            self.hit_button.config(state=tk.DISABLED)
            self.stand_button.config(state=tk.DISABLED)
            self.double_button.config(state=tk.DISABLED)
            self.split_button.config(state=tk.DISABLED)
        else:
            self.hit_button.config(state=tk.NORMAL)
            self.stand_button.config(state=tk.NORMAL)
            if self.game.can_double:
                self.double_button.config(state=tk.NORMAL)
            else:
                self.double_button.config(state=tk.DISABLED)
            if self.game.can_split:
                self.split_button.config(state=tk.NORMAL)
            else:
                self.split_button.config(state=tk.DISABLED)
        # Enable/disable betting controls
        if self.game.bet_size == 0 or self.game.game_over:
            self.place_bet_button.config(state=tk.NORMAL)
            self.bet_entry.config(state=tk.NORMAL)
        else:
            self.place_bet_button.config(state=tk.DISABLED)
            self.bet_entry.config(state=tk.DISABLED)
    
    def place_bet(self):
        """Place a bet and deal the initial cards."""
        try:
            amount = int(self.bet_entry.get())
            if self.game.set_bet(amount):
                self.game.deal_initial_cards()
                self.update_display()
                # Check if game ended immediately (blackjack)
                if self.game.game_over:
                    self.show_result()
                else:
                    self.status_label.config(text=f"Bet placed: ${amount}", fg='green')
            else:
                self.status_label.config(text="Invalid bet amount!", fg='red')
        except ValueError:
            self.status_label.config(text="Please enter a valid number!", fg='red')
    
    def show_result(self):
        """Show the game result."""
        if self.game.game_over:
            if self.game.is_split_game:
                # Handle split game results
                dealer_value = self.game.dealer_hand.get_value()
                results = []
                
                for i, hand in enumerate(self.game.split_hands):
                    player_value = hand.get_value()
                    
                    if hand.is_bust():
                        results.append(f"Hand {i+1}: BUST!")
                    elif self.game.dealer_hand.is_bust():
                        results.append(f"Hand {i+1}: WIN!")
                    elif hand.get_value() == 21 and not self.game.dealer_hand.is_blackjack():
                        results.append(f"Hand {i+1}: WIN!")
                    elif self.game.dealer_hand.is_blackjack() and not hand.is_blackjack():
                        results.append(f"Hand {i+1}: LOSE!")
                    elif player_value > dealer_value:
                        results.append(f"Hand {i+1}: WIN!")
                    elif dealer_value > player_value:
                        results.append(f"Hand {i+1}: LOSE!")
                    else:
                        results.append(f"Hand {i+1}: TIE!")
                
                result = " | ".join(results)
                self.status_label.config(text=result, fg='yellow')
            else:
                # Handle regular game
                player_value = self.game.player_hand.get_value()
                dealer_value = self.game.dealer_hand.get_value()
                
                if self.game.player_hand.is_bust():
                    result = "BUST! You lose!"
                    color = 'red'
                elif self.game.dealer_hand.is_bust():
                    result = "Dealer busts! You win!"
                    color = 'green'
                elif self.game.player_hand.is_blackjack() and not self.game.dealer_hand.is_blackjack():
                    result = "BLACKJACK! You win!"
                    color = 'green'
                elif self.game.dealer_hand.is_blackjack() and not self.game.player_hand.is_blackjack():
                    result = "Dealer has blackjack! You lose!"
                    color = 'red'
                elif player_value > dealer_value:
                    result = "You win!"
                    color = 'green'
                elif dealer_value > player_value:
                    result = "Dealer wins!"
                    color = 'red'
                else:
                    result = "It's a tie!"
                    color = 'yellow'
                
                # Add payout information
                payout = self.game.get_payout()
                result += f" Payout: ${payout}"
                
                self.status_label.config(text=result, fg=color)
    
    def hit(self):
        """Player hits."""
        self.game.hit()
        self.update_display()
        self.show_result()
    
    def stand(self):
        """Player stands."""
        self.game.stand()
        self.update_display()
        self.show_result()
    
    def double(self):
        """Player doubles."""
        self.game.double()
        self.update_display()
        self.show_result()
    
    def split(self):
        """Player splits."""
        self.game.split()
        self.update_display()
        self.show_result()
    
    def start_new_game(self):
        """Start a new game."""
        shuffle_notification = self.game.start_new_game()
        if shuffle_notification:
            self.status_label.config(text=shuffle_notification, fg='yellow')
        else:
            self.status_label.config(text="")
        self.update_display()
    
    def run(self):
        """Start the GUI."""
        self.root.mainloop()

def main():
    """Main function to start the blackjack game."""
    app = BlackjackGUI()
    app.run()

if __name__ == "__main__":
    main() 