import time
import sys
import re
import random
from collections import Counter

from twisted.internet import reactor
from twisted.internet.protocol import ProcessProtocol
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.defer import DeferredQueue, Deferred
from twisted.internet.error import ProcessTerminated, ProcessDone, ProcessExitedAlready


class BattleshipsProcessProtocol(ProcessProtocol):
    def __init__(self, name):
        self.name = name
        self.buf = ''
        self.queue = DeferredQueue()
        self.on_crash = Deferred()
        self.err = ''

    def errReceived(self, data):
        self.err += data

    def outReceived(self, data):
        self.buf += data
        lines = self.buf.split('\n')
        self.buf = lines[-1]
        for l in lines[:-1]:
            self.lineReceived(l)

    def lineReceived(self, line):
        mo = re.match(r'^([A-Z])(\d+)$', line, flags=re.I)
        if mo:
            col = ord(mo.group(1).upper()) - 64
            row = int(mo.group(2))
            self.queue.put((col, row))

    def processExited(self, status):
        if self.err:
            print self.name, "crashed with error:"
            print self.err
        self.on_crash.errback(status)

    def getMove(self):
        return self.queue.get()

    def sendResult(self, result):
        self.transport.write(result + '\n')

    def close(self):
        try:
            self.transport.signalProcess('TERM')
        except ProcessExitedAlready:
            pass

HIT = 'h'
MISS = 'm'
WIN = 'w'
SUNK = 's'



class Grid(object):
    SIZE = 10
    SHIPS = {
        2: 1,
        3: 2,
        4: 1,
        5: 1
    }

    def __str__(self):
        ls = []
        ls.append("   A B C D E F G H I J")
        for row in range(1, self.SIZE + 1):
            r = []
            r.append("%2d" % row)

            def cell(char):
                if (col, row) == self.latest:
                    r.append('\x1b[41m%s\x1b[0m' % char)
                else:
                    r.append(char)
            for col in range(1, self.SIZE + 1):
                try:
                    id, hit = self.grid[(col, row)]
                except KeyError:
                    cell(' ')
                else:
                    if hit:
                        cell('X')
                    else:
                        cell(str(id))
            ls.append(' '.join(r))
        return '\n'.join(ls)

    def coord_in_grid(self, x, y):
        return 0 < x <= self.GRID_SIZE and 0 < y <= self.GRID_SIZE

    def __init__(self):
        self.grid = {}  # state of the board
        self.healths = {}  # healths of each ship
        self.latest = None
        self.place_ships()

    def place_ships(self):
        id = 1
        for length, num in self.SHIPS.items():
            for s in range(num):
                self.place_ship(id, length)
                id += 1

    def place_ship(self, id, length):
        while True:
            orient = random.randint(0, 1)
            if orient == 0:
                x1 = random.randint(1, self.SIZE - length + 1)
                y = random.randint(1, self.SIZE)
                for x in range(x1, x1 + length):
                    if self.grid.get((x, y)):
                        break
                else:
                    for x in range(x1, x1 + length):
                        self.grid[x, y] = (id, False)
                    break
            else:
                x = random.randint(1, self.SIZE)
                y1 = random.randint(1, self.SIZE - length + 1)
                for y in range(y1, y1 + length):
                    if self.grid.get((x, y)):
                        break
                else:
                    for y in range(y1, y1 + length):
                        self.grid[x, y] = (id, False)
                    break
        self.healths[id] = length

    def sink_ship(self, id):
        """Remove a ship from the board."""
        l = 0
        for k, v in self.grid.items():
            if v[0] == id:
                self.grid[k] = 'S', False
                l += 1
        return l

    def attack(self, x, y):
        """Attack the grid cell at x, y."""
        self.latest = (x, y)
        c = self.grid.get((x, y))
        if c is None:
            self.grid[x, y] = '.', False
            return MISS
        id, hit = c
        if id in ('.', 'S'):
            return MISS
        if not hit:
            health = self.healths[id] - 1
            if health > 0:
                self.grid[x, y] = (id, True)
                self.healths[id] = health
            else:
                length = self.sink_ship(id)
                del self.healths[id]
                if not self.healths:
                    return WIN
                else:
                    return SUNK + '\n%d' % length
        return HIT


class Player(object):
    def __init__(self, id, script):
        self.id = id
        self.script = script
        self.grid = Grid()
        self.process = BattleshipsProcessProtocol(script)
        if 'python3' in open(script).readline():
            py = 'python3'
        else:
            py = 'python2'
        reactor.spawnProcess(self.process, sys.executable, args=[py, '-u', script])

    def __str__(self):
        return self.script

    def set_opponent(self, player):
        self.opponent = player
        player.opponent = self


class Game(object):
    MOVE_TIME = 10  # time each script has to compute a move

    def __init__(self, script1, script2):
        self.player1 = Player(1, script1)
        self.player2 = Player(2, script2)
        if script1 == script2:
            self.player1.script += ':1'
            self.player2.script += ':2'
        self.player1.set_opponent(self.player2)

        self.move = 1
        # toss for who goes first
        next_player = random.choice([self.player1, self.player2])
        self.wait_move(next_player)

        self.result = Deferred()

    def wait_move(self, player):
        d = player.process.getMove()
        self.forfeit_timer = reactor.callLater(self.MOVE_TIME, self.forfeit, player)
        d.addCallback(self.on_move, player)
        player.process.on_crash.addErrback(self.on_crash, player)

    def deliver_result(self, winner, outcome):
        if self.result.called:
            return
        self.result.callback((winner, outcome))

    def on_crash(self, failure, player):
        failure.trap(ProcessTerminated, ProcessDone)

        winner = player.opponent.script
        if isinstance(failure.value, ProcessTerminated):
            outcome = '%s died with code %s after %d moves' % (player, failure.value.exitCode, (self.move // 2))
        else:
            outcome = '%s exited' % player
        self.deliver_result(winner, outcome)

    def on_move(self, move, player):
        self.forfeit_timer.cancel()
        self.move += 1
        player.grid.latest = None
        result = player.opponent.grid.attack(*move)
#        print player, move, '->', result
        if result == WIN:
            outcome = "Moves: %d" % (self.move // 2)
            self.deliver_result(player.script, outcome)
            player.process.close()
            player.opponent.process.close()
        else:
            player.process.sendResult(result)
            self.wait_move(player.opponent)

    def forfeit(self, player):
        outcome = "%s forfeited for taking more than %d seconds." % (player, self.MOVE_TIME)
        winner = player.opponent.script
        self.deliver_result(winner, outcome)
        player.process.close()
        player.opponent.process.close()


def ljust(line, length=25):
    linelen = len(re.sub('\x1b' + r'\[\d+m', '', line))
    return line + ' ' * max(0, length - linelen)


class ExhibitionGame(Game):
    def __init__(self, script1, script2, delay):
        self.delay = delay
        super(ExhibitionGame, self).__init__(script1, script2)

    def on_move(self, move, player):
        super(ExhibitionGame, self).on_move(move, player)
        self.draw_boards()
        time.sleep(self.delay)

    def draw_boards(self):
        alines = [self.player1.script] + str(self.player1.grid).splitlines()
        blines = [self.player2.script] + str(self.player2.grid).splitlines()

        print '\x1b[2J',
        for a, b in zip(alines, blines):
            print ljust(a), ljust(b)
        print


class GameRunner(object):
    CONCURRENCY = 20
    GAME_CLS = Game

    def __init__(self, script1, script2, games=1000):
        self.script1 = script1
        self.script2 = script2
        self.games = games
        self.started = 0
        self.finished = 0
        self.tally = Counter()
        self.start_time = time.time()
        for i in range(self.CONCURRENCY):
            self.start_game()

    def start_game(self):
        self.started += 1
        g = Game(self.script1, self.script2)
        g.result.addCallback(self.on_result)

    def on_result(self, result):
        self.finished += 1
        winner, outcome = result
        self.tally[winner] += 1
        print '%4d' % self.finished, winner, '(%s)' % outcome
        if self.finished >= self.games:
            self.print_final_result()
            reactor.stop()
        elif self.started < self.games:
            self.start_game()

    def print_final_result(self):
        duration = time.time() - self.start_time
        if self.script1 == self.script2:
            ks = [
                self.script1 + ':1',
                self.script2 + ':2'
            ]
        else:
            ks = [
                self.script1,
                self.script2
            ]

        for k in ks:
            w = self.tally[k]
            print '%s: %d wins (%0.1f%%)' % (k, w, w * 100.0 / self.games)
        rate = self.finished / duration
        print "%d games in %0.1fs (%0.1f/s)" % (self.finished, duration, rate)


class ExhibitionRunner(object):
    def __init__(self, script1, script2, delay=1.5):
        self.script1 = script1
        self.script2 = script2
        self.delay = delay
        self.start_game()

    def start_game(self):
        g = ExhibitionGame(self.script1, self.script2, delay=self.delay)
        g.result.addCallback(self.on_result)

    def on_result(self, result):
        winner, outcome = result
        print winner, '(%s)' % outcome
        reactor.stop()


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser('%prog [-g <games>] <script> <script>')
    parser.add_option('-g', '--games', type='int', help='Number of games to play', default=1000)
    parser.add_option('-e', '--exhibition', action="store_true", help='Play an exhibition match')
    parser.add_option('-d', '--delay', type='float', help='Delay in exhibition match', default=1.5)

    options, args = parser.parse_args()

    if len(args) != 2:
        parser.error("You must give the names of two scripts to compete.")

    if options.exhibition:
        g = ExhibitionRunner(*args, delay=options.delay)
    else:
        g = GameRunner(*args, games=options.games)
    reactor.run()
