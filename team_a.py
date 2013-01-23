GRID_SIZE = 6
grid = {}
ships = {1:1, 2:2, 3:1, 4:1}

possible_moves = [(x, y) for x in range(1, GRID_SIZE + 1) for y in range(1, GRID_SIZE + 1) if x % 2 ^ y % 2]
possible_moves += [(x, y) for x in range(1, GRID_SIZE + 1) for y in range(1, GRID_SIZE + 1) if not (x % 2 ^ y % 2)]

def min_length():
    for i in range(1, 5):
        if ships[i]:
            return i

def pick_random():
    return possible_moves.pop()

def coord_in_grid(x, y):
    return 0 < x <= GRID_SIZE and 0 < y <= GRID_SIZE

class strafe(object):
    def __init__(self, first_hit):
        print "Strafing from",
        print_location(*first_hit)
        self.first_hit = first_hit

        self.directions = [
            (-1, 0),
            (1, 0),
            (0, 1),
            (0, -1)
        ]
        self.pos = first_hit
        
    def __call__(self):
        global strategy
        if outcome == 'm':
            self.assign_new_direction()
        print "First hit",
        print_location(*self.first_hit)
        while self.directions:
            print "Direction", self.directions[0]
            x, y = self.pos
            dx, dy = self.directions[0]
            self.pos = (x + dx, y + dy)
            if coord_in_grid(*self.pos):
                v = grid.get(self.pos)
                if v == "m":
                    self.assign_new_direction()
                elif v == "h":
                    continue
                else:
                    break
            else:
                self.assign_new_direction()
        possible_moves.remove(self.pos)
        return self.pos

    def assign_new_direction(self):
        try:
            self.directions.pop(0)
        except IndexError:
            strategy = pick_random
            return
        self.pos = self.first_hit
        dir = self.directions[0]
        x, y = dir
        odir = -x, -y
        len = (
            self.consider_direction(dir) +
            1 +
            self.consider_direction(odir)
        )
        if len < min_length():
            self.assign_new_direction()

    def consider_direction(self, dir):
        moved = 0
        pos = self.first_hit
        while True:
            x, y = pos 
            dx, dy = dir
            pos = (x + dx, y + dy)
            if not coord_in_grid(*pos):
                return moved
            if grid.get(pos) == 'm':
                return moved
            moved += 1


def print_location(x, y):
    '''
       >>> print_location(1, 1)
       A1
       >>> print_location(1, 2)
       A2
       >>> print_location(2, 1)
       B1
       >>> print_location(10, 10)
       J10
    '''
    print chr(x + 64) + str(y)


if __name__ == '__main__':
    strategy = pick_random
    while True:
        guess = strategy()
        print_location(*guess)
        while True:
            outcome = raw_input('outcome [h|s|m]:').lower().strip()
            if outcome not in ('h', 'm', 's'):
                print "I don't understand."
            else:
                break
        grid[guess] = 'h' if outcome in 'hs' else 'm'
        if outcome == 'h':
            if not isinstance(strategy, strafe):
                strategy = strafe(guess)
        elif outcome == 's':
            while True:
                l = raw_input('what length of ship?')
                try:
                    l = int(l.strip())
                except ValueError:
                    print 'bad length'
                else:
                    if not ships.get(l, 0):
                        print 'No ships that length'
                    else:
                        break
            ships[l] -= 1
            strategy = pick_random
        elif outcome == 'm':
            pass
