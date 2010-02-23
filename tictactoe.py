#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import itertools

def homogenous(sequence):
    """Considers a sequence and returns an element
    should all elements be "equal". If the sequence is not
    homogenous, None is returned.
    """
    return len(set(sequence)) == 1 and sequence[0] or None


class TicTacToeGame:
    def __init__(self):
        self.board = [' ']*9 # initialize board
        self.turn = 'X'

    def _toggle_turn(self):
        self.turn = self.turn == 'X' and 'O' or 'X'
        
    def winner(self):
        """Returns the character who has won this game, else False."""
        f = [((0, 3, 6), 1), # horizontal
             ((0, 1, 2), 3), # vertical
             ((0,), 4), # diagonal
             ((2,), 2)]
        for (start_positions, skip) in f:
            for start_pos in start_positions:
                h = homogenous(self.board[start_pos::skip][0:3])
                if h and h != ' ':
                    return self.board[start_pos]
                    
    def board_state_str(self):
        return '\n---------\n'.join([
            ' | '.join(self.board[6:9]),
            ' | '.join(self.board[3:6]),
            ' | '.join(self.board[0:3]),
        ])
        
    def state_str(self):
        return '#'.join([self.winner() or ' ', self.turn, ''.join(self.board)])

    def player_action(self, player, pos):
        """Marks a square on the tictactoe table."""
        assert player == self.turn, "Not this players turn"
        assert self.board[pos-1] == ' ', "This square has been marked"
        
        self.board[pos-1] = player

        self._toggle_turn()
        

def local_game():
    """Starts a local two-player game."""
    game = TicTacToeGame()
    
    print """This is a local two-player tictactoe game.
    
Each player marks one square of the 3x3 game table
with a number. The first one to mark three squares horizontally,
vertically or diagonally wins the game. Every square corresponds
to a square number depicted below.
    
    7 | 8 | 9 
    ---------
    4 | 5 | 6
    ---------
    1 | 2 | 3
    
    """
    
    print game.board_state_str()

    for c in itertools.count():
        player = c%2 and 'O' or 'X'
        input_square = int(raw_input("player {0}: ".format(player)))
        game.player_action(player, input_square)
        
        print game.board_state_str()
        if game.winner():
            print game.winner(), "won the game."
            break
            
def network_game(ip, port):
    """Starts a network game."""
    game = TicTacToeGame() # our local copy
    
    print """This is a network two-player tictactoe game.
    
Each player marks one square of the 3x3 game table
with a number. The first one to mark three squares horizontally,
vertically or diagonally wins the game. Every square corresponds
to a square number depicted below.
    
    7 | 8 | 9 
    ---------
    4 | 5 | 6
    ---------
    1 | 2 | 3
    
Connecting to {0}""".format((ip, port))
    import socket
    
    tcpclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpclient.connect((ip, port))
    
    print "Connected, waiting for an opponent."
    
    tcpfile = tcpclient.makefile()
    
    greeting = tcpfile.readline().strip()
    gameid, player = greeting.split('#')
    
    print "Game #{0}, your character is {1}".format(gameid, player)
    
    for c in range(9):
        if game.turn == player: # our turn
            input_square = int(raw_input("Your turn ({0}): ".format(player)))
            tcpclient.send(str(input_square)+'\n')
        else:
            print "Opponents turn..."
            
        state = tcpfile.readline().strip('\n')
        w, game.turn, game.board = state.split("#")
        
        assert len(game.board) == 9, "Illegal response from server."
        
        print game.board_state_str()
        if w != ' ':
            print w, "won the game."
            break
            

def inspect_game(ip, port, gameid):
    import socket
    game = TicTacToeGame()
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(str(gameid), (ip, port))
    state = s.recv(14).strip('\n')
    w, game.turn, game.board = state.split("#")
    
    assert len(game.board) == 9, "Illegal response from server."
    
    print game.board_state_str()
    if w != ' ':
        print w, "won the game."
    

if __name__ == "__main__":
    def usage():
        print """Usage: {0} [IP port [gameid]]
    No arguments launches a two-player local game.
    If IP and port are specified, a multiplayer game is started.
    If gameid is specified, a UDP packet is sent to inspect a game.""".format(sys.argv[0])
    
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
        
    if len(sys.argv) == 3:
        try:
            ip, port = sys.argv[1], int(sys.argv[2])
        except:
            usage()
            sys.exit(1)
        network_game(ip, port)
    elif len(sys.argv) == 4:
        try:
            ip, port, gameid = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
        except:
            usage()
            sys.exit(1)
        inspect_game(ip, port, gameid)
    else:
        local_game()
        
