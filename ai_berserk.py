from ainetwork import *
import random

# a berserk AI. no teamwork. just shoots when enemy appears in front of them

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

dirActionList = [DIRECTION.UP, DIRECTION.DOWN, DIRECTION.LEFT, DIRECTION.RIGHT]

def AI(board, P1robots, P2robots):
    ret = []

    for robot in P1robots:
        if(P2robots == []):
            posAction, dirAction = actionTakeover(robot, board)
        else:
            shotDir, target = dirShot(robot, P2robots)
            if(shotDir != None):
                if(robot.CooldownLaser == 0
                   and(target.CooldownLaser != 0 or random.random() < 0.4)):
                    # able to shoot
                    if(isTeamKill(robot, shotDir, P1robots)):
                        posAction, dirAction = actionTakeover(robot, board)
                    else:
                        posAction = ACTION.SHOT
                        dirAction = shotDir
                else:
                    if(target.CooldownLaser == 0):
                        # try mirror
                        if(robot.CooldownMirror == 0 and random.random() < 0.15):
                            posAction = random.choice([ACTION.PLACEMIRROR1,ACTION.PLACEMIRROR2])
                            dirAction = shotDir
                        else:
                            # must dodge
                            posAction = ACTION.MOVE
                            if(shotDir == DIRECTION.LEFT or shotDir == DIRECTION.RIGHT):
                                dirAction = random.choice([DIRECTION.UP, DIRECTION.DOWN])
                            else:
                                dirAction = random.choice([DIRECTION.LEFT, DIRECTION.RIGHT])
                    else:
                        # do anything
                        posAction, dirAction = actionTakeover(robot, board)
            else:
                approachDir = dirApproach(robot, P2robots)
                if(approachDir != None):
                    posAction = ACTION.MOVE
                    dirAction = approachDir
                else:
                    posAction = ACTION.NOTHING
                    dirAction = DIRECTION.RIGHT
        ret.append(RobotMove(posAction, dirAction))
    return ret

# determine where to shoot.
# return DIRECTION value or None , target enemy
def dirShot(robot, P2robots):
    target = None
    shotDir = None
    for enemy in P2robots:
        if(enemy.Y == robot.Y):
            target = enemy
            if(enemy.X > robot.X):
                shotDir = DIRECTION.DOWN
            else:
                shotDir = DIRECTION.UP
        elif(enemy.X == robot.X):
            target = enemy
            if(enemy.Y > robot.Y):
                shotDir = DIRECTION.RIGHT
            else:
                shotDir = DIRECTION.LEFT
    return shotDir, target

# find direction to approach (aim) the enemy
# return None if already aimed
def dirApproach(robot, P2robots):
    nearestDist = max(HEIGHT+1, WIDTH+1)
    moveDir = None
    oneMore = False
    for enemy in P2robots:
        x_dist = abs(robot.X-enemy.X)
        y_dist = abs(robot.Y - enemy.Y)
        if(x_dist == 1 or y_dist == 1):
            oneMore = True
        if(x_dist < nearestDist):
            nearestDist = x_dist
            if(robot.X < enemy.X):
                moveDir = DIRECTION.DOWN
            elif(robot.X > enemy.X):
                moveDir = DIRECTION.UP
            else:
                moveDir = None
        if(y_dist < nearestDist):
            nearestDist = y_dist
            if(robot.Y < enemy.Y):
                moveDir = DIRECTION.RIGHT
            elif(robot.Y > enemy.Y):
                moveDir = DIRECTION.LEFT
            else:
                moveDir = None
    if(oneMore and random.random()<0.1):
        moveDir = None
        # escape alternating state
    return moveDir

def actionTakeover(robot, board):
    # number of green lands + 2 * of enemy lands is the value of shooting
    #print("enter takeover")
    threshold = 7
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    if(robot.CooldownLaser==0):
        shotValues = [shotValue(robot, board, dir) for dir in directions]
        max_value = max(shotValues)
        max_index = shotValues.index(max_value)
        if(max(shotValues) >= threshold):
            return (ACTION.SHOT, dirActionList[max_index])
    #move
    #print("try finding dirNearGreen")
    if(random.random() < 0.85):
        return (ACTION.MOVE, dirNearGreen(robot, board))
    else:
        return (ACTION.MOVE, random.choice(dirActionList))

def shotValue(robot, board, direction):
    curPos = [robot.X, robot.Y]
    value = 0
    move(curPos, direction)
    while(inBoard(curPos[0], curPos[1])):
        cell = board[curPos[0]][curPos[1]]
        if(cell == PAWN.BLANK):
            value += 1
        elif(cell == PAWN.P2):
            value += 2
        move(curPos, direction)
    return value

def inBoard(x,y):
    return 0<=x and x<HEIGHT and 0<=y and y<WIDTH

def move(pos, direction):
    pos[0] += direction[0]
    pos[1] += direction[1]

# determine where to find greens
def dirNearGreen(robot, board):
    valueVector = [0,0]
    BLANK_VALUE = 3.0
    ENEMY_VALUE = -2.0
    dirMove = DIRECTION.RIGHT
    for x in range(HEIGHT):
        for y in range(WIDTH):
            cellValue = 0
            if(board[x][y]==PAWN.BLANK):
                cellValue = BLANK_VALUE
            elif (board[x][y] == PAWN.P2):
                cellValue = ENEMY_VALUE
            Vx = x-robot.X
            Vy = y-robot.Y
            squaredSumP1 = Vx*Vx + Vy*Vy + 1
            distCost = squaredSumP1**1.5
            valueVector[0] += cellValue*Vx/distCost
            valueVector[1] += cellValue*Vy/distCost
    if(abs(valueVector[0]) > abs(valueVector[1]) ):
        if(valueVector[0] > 0):
            dirMove = DIRECTION.DOWN
        else:
            dirMove = DIRECTION.UP
    else:
        if(valueVector[1] > 0):
            dirMove = DIRECTION.RIGHT
        else:
            dirMove = DIRECTION.LEFT
    return dirMove

def isTeamKill(robot, dir, P1robots):
    dangerous = False
    for friend in P1robots:
        if(friend is robot):
            continue
        else:
            if(friend.Y==robot.Y):
                if(friend.X < robot.X):
                    dangerous = dangerous or dir==DIRECTION.UP
                else:
                    dangerous = dangerous or dir == DIRECTION.DOWN
            if(friend.X==robot.X):
                if(friend.Y < robot.Y):
                    dangerous = dangerous or dir==DIRECTION.LEFT
                else:
                    dangerous = dangerous or dir == DIRECTION.RIGHT
    return dangerous

