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
    
    def should_shuffle(self) -> bool:
        """Check if deck should be shuffled (when 50% or fewer cards remain)."""
        return len(self.cards) <= self.original_size // 2

class Hand:
    """Represents a hand of cards (player or dealer)."""
    
    def __init__(self):
        self.cards = []
    
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
        return len(self.cards) == 2 and self.get_value() == 21
    
    def clear(self):
        """Clear all cards from the hand."""
        self.cards = []

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
    
    def start_new_game(self):
        """Start a new game."""
        # Check if deck needs shuffling
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
        
        # Deal initial cards
        self.player_hand.add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        self.player_hand.add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        
        # Check if double is possible (only on first two cards)
        if len(self.player_hand.cards) == 2:
            self.can_double = True
        
        # Check if split is possible (same value cards)
        if (len(self.player_hand.cards) == 2 and 
            self.player_hand.cards[0].get_value() == self.player_hand.cards[1].get_value()):
            self.can_split = True
        
        return shuffle_notification
    
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
        
        # Buttons frame
        buttons_frame = tk.Frame(self.root, bg='#2c5530')
        buttons_frame.pack(pady=20)
        
        self.hit_button = tk.Button(
            buttons_frame, 
            text="HIT", 
            command=self.hit,
            font=("Arial", 14, "bold"),
            bg='#00C851',
            fg='white',
            width=10,
            height=2,
            relief=tk.RAISED,
            activebackground='#00A041',
            activeforeground='white'
        )
        self.hit_button.pack(side=tk.LEFT, padx=10)
        
        self.stand_button = tk.Button(
            buttons_frame, 
            text="STAND", 
            command=self.stand,
            font=("Arial", 14, "bold"),
            bg='#FF4444',
            fg='white',
            width=10,
            height=2,
            relief=tk.RAISED,
            activebackground='#CC3333',
            activeforeground='white'
        )
        self.stand_button.pack(side=tk.LEFT, padx=10)
        
        self.double_button = tk.Button(
            buttons_frame, 
            text="DOUBLE", 
            command=self.double,
            font=("Arial", 14, "bold"),
            bg='#FF6B35',
            fg='white',
            width=10,
            height=2,
            relief=tk.RAISED,
            activebackground='#E55A2B',
            activeforeground='white'
        )
        self.double_button.pack(side=tk.LEFT, padx=10)
        
        self.split_button = tk.Button(
            buttons_frame, 
            text="SPLIT", 
            command=self.split,
            font=("Arial", 14, "bold"),
            bg='#9932CC',
            fg='white',
            width=10,
            height=2,
            relief=tk.RAISED,
            activebackground='#7A28A3',
            activeforeground='white'
        )
        self.split_button.pack(side=tk.LEFT, padx=10)
        
        self.new_game_button = tk.Button(
            buttons_frame, 
            text="NEW GAME", 
            command=self.start_new_game,
            font=("Arial", 14, "bold"),
            bg='#4285F4',
            fg='white',
            width=10,
            height=2,
            relief=tk.RAISED,
            activebackground='#3367D6',
            activeforeground='white'
        )
        self.new_game_button.pack(side=tk.LEFT, padx=10)
        
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
        if self.game.game_over:
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
        if self.game.is_split_game and self.game.split_hands:
            # Display split hands
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
            # Display regular hand
            player_cards = [str(card) for card in self.game.player_hand.cards]
            player_text = f"Cards: {', '.join(player_cards)}"
            player_value = self.game.player_hand.get_value()
            
            self.player_hand_label.config(text=player_text)
            self.player_value_label.config(text=f"Value: {player_value}")
        
        # Update stats
        self.player_score_label.config(text=f"Player: {self.game.player_wins}")
        self.dealer_score_label.config(text=f"Dealer: {self.game.dealer_wins}")
        self.ties_label.config(text=f"Ties: {self.game.ties}")
        self.deck_status_label.config(text=f"Deck: {self.game.deck.get_remaining_percentage():.0f}%")
        
        # Update button states
        if self.game.game_over:
            self.hit_button.config(state=tk.DISABLED)
            self.stand_button.config(state=tk.DISABLED)
            self.double_button.config(state=tk.DISABLED)
            self.split_button.config(state=tk.DISABLED)
        else:
            self.hit_button.config(state=tk.NORMAL)
            self.stand_button.config(state=tk.NORMAL)
            
            # Enable/disable double button
            if self.game.can_double:
                self.double_button.config(state=tk.NORMAL)
            else:
                self.double_button.config(state=tk.DISABLED)
            
            # Enable/disable split button
            if self.game.can_split:
                self.split_button.config(state=tk.NORMAL)
            else:
                self.split_button.config(state=tk.DISABLED)
    
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
                    elif hand.is_blackjack() and not self.game.dealer_hand.is_blackjack():
                        results.append(f"Hand {i+1}: BLACKJACK!")
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