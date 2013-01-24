import random

def get_letter(n):
    itoa = {0:"A", 1:"B", 2:"C",3:"D",4:"E",5:"F", 6:"G", 7:"H", 8:"I", 9:"J"}
    return itoa[n]
    
class cell(object):
    def __init__(self, x, y):
        self.state = "?"
        self.x = get_letter(x)
        self.y = y + 1
        self.raw_x = x
        self.raw_y = y

    def has_miss(self,grid,x,y):
        if x<0 or y<0: return True
        if x>9 or y>9: return True
        return grid[y][x].state == 'm'

    def has_hit(self,grid,x,y):
        if x<0 or y<0: return False
        if x>9 or y>9: return False
        # Don't include 's' in the search
        return grid[y][x].state == 'h'
        # Alternatively include the 's'
        #if grid[y][x].state in ['h','s']:
        #    return True
        
    def is_surrounded_by_misses(self,grid):
        """ Are all the adjacent cells in grid misses? """
        return self.has_miss(grid,self.raw_x + 1, self.raw_y) and self.has_miss(grid,self.raw_x - 1, self.raw_y) and self.has_miss(grid,self.raw_x, self.raw_y + 1) and self.has_miss(grid,self.raw_x, self.raw_y - 1)
        
    def has_double_adjacent_hit(self, grid):
        if self.has_hit(grid,self.raw_x + 1, self.raw_y) and self.has_hit(grid,self.raw_x + 2, self.raw_y): return True
        if self.has_hit(grid,self.raw_x - 1, self.raw_y) and self.has_hit(grid,self.raw_x - 2, self.raw_y): return True
        if self.has_hit(grid,self.raw_x, self.raw_y + 1) and self.has_hit(grid,self.raw_x, self.raw_y + 2): return True
        if self.has_hit(grid,self.raw_x, self.raw_y - 1) and self.has_hit(grid,self.raw_x, self.raw_y - 2): return True
        return False
                
    def has_adjacent_hit(self, grid):
        """ Do any of the adjacent cells in grid have a hit? """
        if self.has_hit(grid,self.raw_x + 1, self.raw_y): return True
        if self.has_hit(grid,self.raw_x - 1, self.raw_y): return True
        if self.has_hit(grid,self.raw_x, self.raw_y + 1): return True
        if self.has_hit(grid,self.raw_x, self.raw_y - 1): return True
        return False

class board(object):
    def __init__(self):
        self.last_cell=None
        self.grid = [ [cell(x,y) for x in range(0,10)] for y in range(0,10)]
    
    def print_board(self):
        print "   A B C D E F G H I J"
        count = 1
        for line in self.grid:
            print "%02d" % (count,),
            for cell in line:
                print cell.state,
            print
            count = count + 1
            
    def get_next_cell(self):
        # Make a list of all cells adjacent to hits not off the board
        double_adjacent_list = []
        adjacent_list = []
        for line in self.grid:
            for cell in line:
                if cell.state == '?':
                    # Check double adjacent cells                    
                    if cell.has_double_adjacent_hit(self.grid):
                        double_adjacent_list.append(cell)
                    # Check adjacent cells
                    if cell.has_adjacent_hit(self.grid):
                        adjacent_list.append(cell)
        if len(double_adjacent_list) > 0:
            return random.choice(double_adjacent_list)
        if len(adjacent_list) > 0:
            return random.choice(adjacent_list)
            
        random_line = random.choice(self.grid)
        random_cell = random.choice(random_line)
        return random_cell
        
    def get_next_move(self):
        for line in self.grid:
            for cell in line:
                if cell.state == '?':
                    # Check if surrounded by misses
                    if cell.is_surrounded_by_misses(self.grid):
                        cell.state='i'
        while True:
            cell = self.get_next_cell()
            if cell.state=='?':
                self.last_cell = cell
                return cell.x, cell.y
        
    def set_last_move_state(self,state):
        self.last_cell.state=state
        
if __name__=='__main__':
    b = board()
    #b.print_board()
    print '%s%d' % b.get_next_move()
    a = True
    sunk_count = 0
    #print 'To quit type & enter: "end"'
    while a:
        var = raw_input('hit, miss or sunk?:\n')
        if var == 'end':
            a = False
        else:
            if var.upper() not in ['H', 'M', 'S']:
                print "please try again"
                continue
            move = var.strip().lower()
            b.set_last_move_state(move)
            # b.print_board()
            if move == 's': 
                length = raw_input('length?\n')
                sunk_count += 1
            if sunk_count == 5:
                print "BATTLESHIPS!"
                break
            print '%s%d' % b.get_next_move()
            
