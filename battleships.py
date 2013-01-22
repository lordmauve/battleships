import random

grid = {}

def pick_random():
    while True:
        x = random.randint(1, 11)
        y = random.randint(1, 11)
        if (x, y) not in grid:
            return x, y

def coord_in_grid(x, y):
    return 0 < x < 11 and 0 < y < 11

class strafe(object):
    def __init__(self, first_hit):
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
        if outcome is 'm':
            self.assign_new_direction()
        while self.directions:
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
        return self.pos

    def assign_new_direction(self):
        try:
            self.directions.pop(0)
        except IndexError:
            strategy = pick_random
        self.pos = self.first_hit

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
            if strategy is not strafe:
                strategy = strafe(guess)
        elif outcome == 's':
            strategy = pick_random
        elif outcome == 'm':
            pass
