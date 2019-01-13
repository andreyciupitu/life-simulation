INIT_POP = 20
MAX_LIFE = 500
AGE_VAR = 100
BUDDING_PROB = 10
BUDDING_MIN_RES = 100
MIN_BUDDING_AGE = 150
MAX_BUDDING_AGE = 350
BUDDING_TIME = 1
BUD_FACTOR = 2
FOOD_SIZE = 100
FOOD_BUILD = 1
POWER_TO_STAY = 1
VAPOUR_TO_STAY = 1
POWER_TO_MOVE = 2
VAPOUR_TO_MOVE = 2
MAX_RES = 300
SEE_RANGE = 25


def read_params(filename):
    # Bullshit ahead !!!!!!!
    global INIT_POP
    global MAX_LIFE
    global AGE_VAR
    global BUDDING_PROB
    global BUDDING_MIN_RES
    global MIN_BUDDING_AGE
    global MAX_BUDDING_AGE
    global BUDDING_TIME
    global BUD_FACTOR
    global FOOD_SIZE
    global FOOD_BUILD
    global POWER_TO_STAY
    global VAPOUR_TO_STAY
    global POWER_TO_MOVE
    global VAPOUR_TO_MOVE
    global MAX_RES
    global SEE_RANGE

    # Read lines from file
    with open(filename) as f:
        lines = [line.split() for line in f]

        # More bullshit dawg
        INIT_POP = int(lines[0][0])
        MAX_LIFE = int(lines[1][0])
        AGE_VAR = int(lines[2][0])
        BUDDING_PROB = int(lines[3][0])
        BUDDING_MIN_RES = int(lines[4][0])
        MIN_BUDDING_AGE = int(lines[5][0])
        MAX_BUDDING_AGE = int(lines[5][0])
        BUDDING_TIME = int(lines[7][0])
        BUD_FACTOR = int(lines[8][0])
        FOOD_SIZE = int(lines[9][0])
        FOOD_BUILD = int(lines[10][0])
        POWER_TO_STAY = int(lines[11][0])
        VAPOUR_TO_STAY = int(lines[12][0])
        POWER_TO_MOVE = int(lines[13][0])
        VAPOUR_TO_MOVE = int(lines[14][0])
        MAX_RES = int(lines[15][0])
        SEE_RANGE = int(lines[16][0])
