from ainetwork import *
import random
import time

HEIGHT = 0
WIDTH = 0
CD_MIRROR = 0
CD_LASER = 0
GAME_TURN = 0

def Init(height, width, cooldownMirror, cooldownLaser, gameTurn):
    global HEIGHT, WIDTH, CD_MIRROR, CD_LASER, GAME_TURN
    HEIGHT = height
    WIDTH = width
    CD_MIRROR = cooldownMirror
    CD_LASER = cooldownLaser
    GAME_TURN = gameTurn
    print(height, width, cooldownMirror, cooldownLaser, gameTurn)

GAME_ELAPSED = 0

inDebug = 10

def AI(board, P1robots, P2robots):
    global GAME_ELAPSED, inDebug
    ret = []
    GAME_ELAPSED += 1

    if(P1robots == []): return []

    DM = DangerMap(board, P1robots, P2robots)
    '''
    for j in range(100):
        ret = []
        for i in P1robots:

        if(DM.dangerLevel(P1robots, ret) >= DangerLevel.direct):
            continue
        else:
            return ret
    '''
    actionList = [ACTION.MOVE, ACTION.NOTHING]
    dirList = [DIRECTION.LEFT, DIRECTION.RIGHT, DIRECTION.UP, DIRECTION.DOWN]

    possibleMoves = [RobotMove(ACTION.MOVE, DIRECTION.LEFT),
                     RobotMove(ACTION.MOVE, DIRECTION.RIGHT),
                     RobotMove(ACTION.MOVE, DIRECTION.UP),
                     RobotMove(ACTION.MOVE, DIRECTION.DOWN),
                     RobotMove(ACTION.NOTHING, DIRECTION.LEFT)]

    if(len(P1robots) == 1):
        for rm1 in possibleMoves:
                rMoves = [rm1]
                if(DM.dangerLevel(P1robots, rMoves) < DangerLevel.direct):
                    return rMoves

    if(len(P1robots) == 2):
        for rm1 in possibleMoves:
            for rm2 in possibleMoves:
                    rMoves = [rm1, rm2]
                    if(DM.dangerLevel(P1robots, rMoves) < DangerLevel.direct):
                        return rMoves

    if(len(P1robots) == 3):
        for rm1 in possibleMoves:
            for rm2 in possibleMoves:
                for rm3 in possibleMoves:
                    rMoves = [rm1, rm2, rm3]
                    if(DM.dangerLevel(P1robots, rMoves) < DangerLevel.direct):
                        # we have it
                        if(inDebug>0):
                            inDebug -= 1
                            dbfile = open('dblog.txt', 'a')
                            dbfile.write("\n"+DM.printMap()+"\n")
                            dbfile.write(rMoves.__str__()+"\n\n")
                            dbfile.close()
                        return rMoves

    for i in P1robots:
        ret.append(RobotMove(random.choice(actionList), random.choice(dirList)))

    return ret


class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

class DangerLevel:
    collision = 9
    direct = 7
    mirrored = 5
    possiblyMirrored = 3
    notDie = 1

class DangerMap():
    lasers = [] # list of independent lasers
    map = [] # DMcell[0~height+1][0~width+1]


    class MapCell():
        N = 0 #fixed mirrors
        Z = 1
        X1 = 2 #unfixed mirrors
        X2 = 3
        X3 = 4
        enemy = 5 #enemy body (possibly cannot move or put a mirror to it)
        empty = 6 #empty
        boundary = 7 #boundary
        enemyLand = 8
        friend = 9

        dangerLevel = 0

        state = []

        def __init__(self):
            self.state = []
            for i in range(10):
                self.state.append(False)

        def mark(self, property):
            self.state[property] = True

        def has(self, property):
            return self.state[property]

    class Laser():
        # a tree of possible lasers
        headSegment = None
        shotBy = 0 # 1 2 3 : enemies

        class LaserSegment():
            # edges of laser tree
            p0 = 0
            length = 0
            dir = (0,0)
            travelDist = 0

            children = [] # laser reflected within this segment
            colLeft = []  # ex) [0,1,1,0] : for laser from 2

            def __init__(self, p0, dir, length, colLeft, colPrev, travelDist, parent=None):
                self.p0 = p0 # exclusive danger
                self.length = length # inclusive danger
                self.dir = dir # ex) (1,0)
                self.colLeft = colLeft # assume copied
                #print("init colleft "+str(colLeft)+" prev: "+str(colPrev))
                self.colLeft[colPrev] -= 1
                self.travelDist = travelDist
                self.parent = parent

            def passes(self, p1):
                if(p1.x == self.p0.x):
                    if(self.dir[1]>0
                       and p1.y > self.p0.y
                       and self.p0.y + self.length >= p1.y):
                        return True
                    elif(self.dir[1]<0
                         and p1.y < self.p0.y
                         and self.p0.y + self.length <= p1.y):
                        return True
                if(p1.y == self.p0.y):
                    if(self.dir[0]>0
                       and p1.x > self.p0.x
                       and self.p0.x + self.length >= p1.x):
                        return True
                    elif(self.dir[0]<0
                         and p1.x < self.p0.x
                         and self.p0.x + self.length <= p1.x):
                        return True
                return False

            def printParentChain(self):
                print((self.p0.x,self.p0.y))
                s = str((self.p0.x,self.p0.y))+'\n'
                if(self.parent != None):
                    return s+self.parent.printParentChain()
                else:
                    return s

            def stretch(self, map):
                # recursively stretch to make a tree of segments

                # if empty, progess to front
                # if N or collidable X, branch.
                # if Z or collidable X, branch.
                # if boundary or too long travelDist, stop.

                currentPos = [self.p0.x,
                              self.p0.y]

                self.children = []
                self.length = 0
                self.parent = None

                def branchDir(dir, type):
                    if(type == 'N'):
                        return (dir[1], dir[0])
                    elif(type == 'Z'):
                        return (-dir[1], -dir[0])


                while True:
                    currentPos[0] += self.dir[0]
                    currentPos[1] += self.dir[1]
                    cell = map[currentPos[0]+1][currentPos[1]+1]
                    if(cell.has(cell.boundary) or self.travelDist > 30):
                        break
                    if(sum(self.colLeft[1:4]) < 2):
                        cell.dangerLevel = max(DangerLevel.possiblyMirrored, cell.dangerLevel)
                    elif(self.colLeft[0] < 0):
                        cell.dangerLevel = max(DangerLevel.mirrored, cell.dangerLevel)
                    else:
                        #<DB>
                        if(currentPos == [0, 6] and GAME_ELAPSED == 8):
                            s = self.printParentChain()
                            dbfile = open('dblog.txt', 'a')
                            dbfile.write("\nset dangerous [0,6] at turn 8, parent chain:\n"+s+"\n")
                            dbfile.close()                            
                        #</DB>
                        cell.dangerLevel = max(DangerLevel.direct, cell.dangerLevel)

                    self.length += 1
                    X = (cell.X1, cell.X2, cell.X3)
                    proceed = True
                    for i in range(3):
                        if(cell.has(X[i]) and self.colLeft[i+1] != 0):
                            self.children.append(
                                DangerMap.Laser.LaserSegment(Point(currentPos[0], currentPos[1]),
                                              branchDir(self.dir, 'N'),
                                              0,self.colLeft[:],i+1,
                                              self.travelDist + self.length+1, self)
                            )
                            self.children.append(
                                DangerMap.Laser.LaserSegment(Point(currentPos[0], currentPos[1]),
                                              branchDir(self.dir, 'Z'),
                                              0,self.colLeft[:],i+1,
                                              self.travelDist + self.length+1, self)
                            )

                    if(cell.has(cell.Z)):
                        self.children.append(
                            DangerMap.Laser.LaserSegment(Point(currentPos[0], currentPos[1]),
                                            branchDir(self.dir, 'Z'),
                                            0,self.colLeft[:],0,
                                            self.travelDist + self.length+1, self)
                        )
                        proceed = False
                    if(cell.has(cell.N)):
                        self.children.append(
                            DangerMap.Laser.LaserSegment(Point(currentPos[0], currentPos[1]),
                                            branchDir(self.dir, 'N'),
                                            0,self.colLeft[:],0,
                                            self.travelDist + self.length+1, self)
                        )
                        proceed = False
                    if(not proceed):
                        break

                for child in self.children:
                    child.stretch(map)
                pass


        def __init__(self, p, dir, shotBy):
            self.p = p
            self.dir = dir
            self.shotBy = shotBy

        def makeTree(self, map):
            # shoot laser and make tree of segments
            if(self.p == Point(6, 6) and GAME_ELAPSED == 8):
                dbfile = open('dblog.txt', 'a')
                dbfile.write("\nmake tree starting from [6,6] at turn 8")
                dbfile.close()                            
            #</DB>            
            self.headSegment = self.LaserSegment(self.p, self.dir, 0, [0,1,1,1], self.shotBy, 0)
            self.headSegment.stretch(map)
            pass

    def fillMap(self, board, P1robots, P2robots):
        # fill self.map with properties according to possible
        # actions of enemy robots
        # also initialize lasers

        # read board status
        self.map = []
        self.lasers = []
        for xi in range(HEIGHT+2):
            row = []
            for yi in range(WIDTH+2):
                newCell = self.MapCell()
                if(xi==0 or xi==HEIGHT+1 or yi==0 or yi==WIDTH+1):
                    newCell.mark(self.MapCell.boundary)
                else:
                    boardCell = board[xi-1][yi-1]
                    if(boardCell == PAWN.P1MIRROR1 or boardCell == PAWN.P2MIRROR1):
                        newCell.mark(self.MapCell.N)
                    elif(boardCell == PAWN.P1MIRROR2 or boardCell == PAWN.P2MIRROR2):
                        newCell.mark(self.MapCell.Z)
                    elif(boardCell == PAWN.BLANK or boardCell == PAWN.P1 ):
                        newCell.mark(self.MapCell.empty)
                    elif(boardCell == PAWN.P2):
                        newCell.mark(self.MapCell.enemyLand)
                row.append(newCell)
            self.map.append(row)
        
        for friend in P1robots:
            self.map[friend.X+1][friend.Y+1].mark(self.MapCell.friend)

        # enemy movements
        dirs = [(1,0),(-1,0),(0,1),(0,-1)]
        i = 0 # enemy number
        for enemy in P2robots:
            i += 1
            self.map[enemy.X+1][enemy.Y+1].mark(self.MapCell.enemy)
            # possible enemy mirrors
            if(enemy.CooldownMirror == 0):
                for dir in dirs:
                    if(i == 1):
                        self.map[enemy.X+1+dir[0]][enemy.Y+1+dir[1]].mark(self.MapCell.X1)
                    if(i == 2):
                        self.map[enemy.X+1+dir[0]][enemy.Y+1+dir[1]].mark(self.MapCell.X2)
                    if(i == 3):
                        self.map[enemy.X+1+dir[0]][enemy.Y+1+dir[1]].mark(self.MapCell.X3)

            # possible enemy lasers
            if(enemy.CooldownLaser == 0):
                for dir in dirs:
                    self.lasers.append(self.Laser(Point(enemy.X, enemy.Y), dir, i))

    def __init__(self, board, P1robots, P2robots):
        self.fillMap(board, P1robots, P2robots)
        for laser in self.lasers:
            laser.makeTree(self.map)

    def simulateMap(self, rMoves):
        # currently no friend mirror/laser simulation
        pass

    def recoverMap(self):
        # reverse of simulateMap
        pass

    def dangerLevel(self, P1robots, rMoves):
        self.simulateMap(rMoves)
        poslist = []
        for i in range(len(P1robots)):
            pos = Point(P1robots[i].X, P1robots[i].Y)
            action = rMoves[i].action
            direction = rMoves[i].direction
            if(action == ACTION.MOVE):
                if(direction == DIRECTION.DOWN):
                    pos.x += 1
                elif(direction == DIRECTION.UP):
                    pos.x -= 1
                elif(direction == DIRECTION.RIGHT):
                    pos.y += 1
                elif(direction == DIRECTION.LEFT):
                    pos.y -= 1
                else:
                    pass

            if(pos in poslist):
                return DangerLevel.collision
            else:
                poslist.append(pos)

        dangerLevels = [self.dangerLevelPos(pos) for pos in poslist]

        self.recoverMap()
        return max(dangerLevels)

    def dangerLevelPos(self, p):
        cell = self.map[p.x+1][p.y+1]
        if(cell.has(self.MapCell.boundary) or cell.has(self.MapCell.enemyLand)
           or cell.has(self.MapCell.N) or cell.has(self.MapCell.Z)):
            return DangerLevel.collision
        return cell.dangerLevel

    def printMap(self):
        s = str(GAME_ELAPSED)
        for i in range(HEIGHT+2):
            s += "\n"
            for j in range(WIDTH+2):
                c = '  '
                cell = self.map[i][j]
                if(cell.has(self.MapCell.boundary)):
                    c = ' X'
                elif(cell.has(self.MapCell.enemy)):
                    c = ' E'
                elif(cell.has(self.MapCell.friend)):
                    c = ' F'
                else:
                    c = ' '+str(cell.dangerLevel)
                s += c
        print(s)
        return s

'''
    while(True):
        s = input()
        s = 'print('+s+')'
        exec(s)
'''

def tmain():
    global HEIGHT, WIDTH
    HEIGHT = 7
    WIDTH = 13
    board = []
    for i in range(HEIGHT):
        row = []
        for j in range(WIDTH):
            row.append(PAWN.BLANK)
        board.append(row)
    P1robots = [
        Robot(0,0,0,0),
        Robot(1,0,0,0),
        Robot(2,0,0,0)
        ]
    P2robots = [
        Robot(HEIGHT-1,WIDTH-1,0,0),
        Robot(HEIGHT-2,WIDTH-1,0,0),
        Robot(HEIGHT-3,WIDTH-1,0,0)
        ]

    DM = DangerMap(board, P1robots, P2robots)
    DM.printMap()

def t2main():
    global HEIGHT, WIDTH
    HEIGHT = 7
    WIDTH = 13

    s ='''
<R1> <R1> <R1> .... .... .... .... .... <R2> .... .... .... ....
.P1. .P1. .... .... .... .... .... .... .P2. .... .... -2Z- .P2.
.P2. .P2. .P2. .P2. .P2. .P2. .P2. .P2. .P2. .P2. .P2. .P2. <R2>
.... .... .... .... .... .... .... .... .P2. .... .... .... .P2.
.... .... .... .... .... .... .... .... .... .... .... .... .P2.
.... .... .... .... .... .... .... .... .... .... .... .... .P2.
.... .... .... .... .... .... .... .... .... .... .... .... .P2.
    '''

    board, P1robots, P2robots = translateBoard(s)
    DM = DangerMap(board, P1robots, P2robots)
    DM.printMap()
    '''
    def helper(P1robots, DM):
        possibleMoves = [RobotMove(ACTION.MOVE, DIRECTION.LEFT),
                         RobotMove(ACTION.MOVE, DIRECTION.RIGHT),
                         RobotMove(ACTION.MOVE, DIRECTION.UP),
                         RobotMove(ACTION.MOVE, DIRECTION.DOWN),
                         RobotMove(ACTION.NOTHING, DIRECTION.LEFT)]

        if(len(P1robots) < 3):
            a = a/0
        if(len(P1robots) == 3):
            for rm1 in possibleMoves:
                for rm2 in possibleMoves:
                    for rm3 in possibleMoves:
                        rMoves = [rm1, rm2, rm3]
                        if(DM.dangerLevel(P1robots, rMoves) < DangerLevel.direct):
                            return rMoves
        print("cant find")

    rMoves = helper(P1robots, DM)
    print(rMoves)
    print(DM.dangerLevel(P1robots, rMoves))
        '''

    moves = AI(board, P1robots, P2robots)
    print(moves)

def translateBoard(s):
    res = ""
    L = s.lstrip().split()
    board = []
    P1robots = []
    P2robots = []
    for i in range(HEIGHT):
        row = []
        for j in range(WIDTH):
            cw = L[i*WIDTH + j]
            if(cw == '....'):
                row.append(PAWN.BLANK)
            elif(cw == '.P1.'):
                row.append(PAWN.P1)
            elif(cw == '.P2.'):
                row.append(PAWN.P2)
            elif(cw == '-1N-'):
                row.append(PAWN.P1MIRROR1)
            elif(cw == '-1Z-'):
                row.append(PAWN.P1MIRROR2)
            elif(cw == '-2N-'):
                row.append(PAWN.P2MIRROR1)
            elif(cw == '-2Z-'):
                row.append(PAWN.P2MIRROR2)
            elif(cw == '<R1>'):
                row.append(PAWN.P1)
                P1robots.append(
                    Robot(i,j,0,0)
                    )
            elif(cw == '<R2>'):
                row.append(PAWN.P2)
                P2robots.append(
                    Robot(i,j,0,0)
                    )
        board.append(row)

    return board, P1robots, P2robots
