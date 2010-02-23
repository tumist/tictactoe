#!/usr/bin/python
import sys
import SocketServer
import threading
import tictactoe


class TicTacToeNetworkGame(tictactoe.TicTacToeGame):
    # TTTConnectionHandler instances filled out in TTTServer.join_game
    client_X_ch = None
    client_O_ch = None
    
    def network_announce_state(self):
        """Write out the state string to both connection handlers."""
        self.client_X_ch.wfile.write(self.state_str()+'\n')
        self.client_O_ch.wfile.write(self.state_str()+'\n')
        

class TTTServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    
    def __init__(self, addr):
        self.games = []
        self.waiting_game = None
        self.waiting_lock = threading.Semaphore(0)
        
        SocketServer.TCPServer.__init__(self, addr, TTTConnectionHandler)
        
        print "Server up on {0}".format(addr)
        self._setup_udp_server(addr)
        
    def _setup_udp_server(self, addr):
        class DGRAMHandler(SocketServer.BaseRequestHandler):
            def handle(self):
                data = self.request[0].strip()
                socket = self.request[1]
                
                print "Datagram from {0} wants to inspect game {1}"\
                    .format(self.client_address, data)
                    
                try:
                    socket.sendto(self.server.games[int(data)].state_str(),
                        self.client_address)
                except Exception, e:
                    # game does not exists, etc: silent treatment
                    print "UDP Exception: {0}".format(e)
                    pass
                    
        self.udpserver = SocketServer.UDPServer(addr, DGRAMHandler)
        self.udpserver.games = self.games
        self.udpthread = threading.Thread(target=self.udpserver.serve_forever)
        self.udpthread.daemon = True
        self.udpthread.start()
        
        print "UDP Server up on {0}".format(addr)

    def join_game(self, connection_handler):
        if self.waiting_game:
            g = self.waiting_game
            g.client_O_ch = connection_handler
            self.waiting_lock.release()
            self.waiting_game = None
            self.games.append(g)
            return (self.games.index(g), 'O', g)
        else:
            g = TicTacToeNetworkGame()
            g.client_X_ch = connection_handler
            self.waiting_game = g
            self.waiting_lock.acquire()
            return (self.games.index(g), 'X', g)


class TTTConnectionHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        print "TCP Client {0} waiting for game".format(self.client_address)
        gameid, player, game = self.server.join_game(self)
        
        self.wfile.write("{0}#{1}\n".format(gameid, player))
        
        for c in range(5):
            input = self.rfile.readline().strip()
            try:
                p = int(input)
                game.player_action(player, p)
            except:
                continue # silent treatment
            
            #
            game.network_announce_state()
            if game.winner():
                print "{0} won game #{1}".format(player, gameid)
                break # connection is dropped

if __name__ == "__main__":
    try:
        (port, host) = int(sys.argv[1]), sys.argv[2]
    except:
        print "Usage: {0} port address".format(sys.argv[0])
        sys.exit(1)

    server = TTTServer((host, port))
    server.serve_forever()
