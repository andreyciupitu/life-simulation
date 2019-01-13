import random
import queue
import params

# Directions
NORTH = "north"
SOUTH = "south"
EAST = "east"
WEST = "west"
DIRECTIONS = {NORTH: (0, -1), SOUTH: (0, 1), WEST: (-1, 0), EAST: (1, 0)}
OPPOSITE = {NORTH: SOUTH, SOUTH: NORTH, WEST: EAST, EAST: WEST}

# State index
AVAILABLE = 0
WATER_DIR = 1
FRIENDS_DIR = 2
IN_FOREST = 3
CENTER_DIR = 4

# Commands
MOVE = "move"
STAY = "stay"
EAT = "consume"

# Tile types
NORMAL = "normal"
WATER = "water"
FOREST = "forest"


class MapTile:
    def __init__(self):
        self.type = NORMAL
        self.blips = []
        self.value = 0


class Blip:
    """
    An agent that takes part in the simulation.
    """
    EXPLORE_CHANCE = 0.25

    def __init__(self, lifetime):
        self.lifetime = lifetime
        self.age = 0
        self.strength = params.MAX_RES
        self.vapors = params.MAX_RES
        self.pregnant = False
        self.due_time = 0
        self.threshold = max(params.MAX_RES / 2, params.BUDDING_MIN_RES)

    def decide_action(self, state):
        """
        Decides the next action of the blip based on its current state
        :param state: A tuple (available directions, direction to water, direction to other blips)
        :return: A tuple (move type from [MOVE, STAY, EAT], arg)
        """
        # If it's old it just wanders around till it's dead
        if self.age > params.MAX_BUDDING_AGE:
            return MOVE, random.choice(state[AVAILABLE])

        # Go to the center to make the baby
        if self.pregnant:
            return MOVE, state[CENTER_DIR]

        # If I need water
        if self.vapors < self.threshold and self.vapors <= self.strength:
            # If I don't know where the water is
            # check with the other blips, maybe they know
            if not state[WATER_DIR]:
                return MOVE, state[FRIENDS_DIR]

            # Drink water if near the lake
            if state[WATER_DIR] not in state[AVAILABLE]:
                return EAT, params.MAX_RES - self.vapors

            # Go to water source if available
            return MOVE, state[WATER_DIR]

        # If I need to eat
        if self.strength < self.threshold:
            if not state[IN_FOREST] and EAST in state[AVAILABLE]:
                return MOVE, EAST
            else:
                if random.random() < 0.5:
                    return MOVE, random.choice(state[AVAILABLE])
                else:
                    return EAT, params.BUDDING_MIN_RES - self.strength + params.POWER_TO_STAY


        # If I'm ok, then wander around or explore the rest of the map
        if random.random() < Blip.EXPLORE_CHANCE:
            return MOVE, WEST
        else:
            return MOVE, random.choice(state[AVAILABLE])

    def get_status(self):
        """
        Returns the current status of the blip.

        :return: A tuple (age%, vapors%, strength%)
        """
        return 1 - self.age / self.lifetime, self.vapors / params.MAX_RES, self.strength / params.MAX_RES


class World:
    """
    Simulates the environment of the game.
    Controls and executes the commands of the blips.
    """

    def __init__(self, dimensions, lake_size, forest_width):
        self.width, self.height = dimensions
        self.lake_size = lake_size
        self.forest_width = forest_width

        # Quick access for tiles
        self.blips = {}
        self.food_tiles = []
        self.water_tiles = []

        # Init map
        self.map = [[MapTile() for _ in range(self.width)] for _ in range(self.height)]

        # Assign Forest Tiles in the East
        for y in range(self.height):
            for x in range(self.width - forest_width, self.width):
                self.map[y][x].value = params.FOOD_SIZE
                self.map[y][x].type = FOREST
                self.food_tiles.append((x, y))

        # Create lake in the West
        lake_start = random.randint(0, self.height - lake_size)
        for y in range(lake_size):
            for x in range(lake_size):
                self.map[lake_start + y][x].type = WATER
                self.water_tiles.append((x, lake_start + y))

        # Init blips
        for i in range(params.INIT_POP):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)

            # Spawn only on free tiles
            while self.map[y][x].type != NORMAL:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)

            self.spawn_blip((x, y))

        # Compute shortest distance
        # to water from each tile
        self.water_distance = None
        for y in range(lake_size):
            for x in range(lake_size):
                self.water_distance = self.compute_distances((x, lake_start + y), self.water_distance)

    def turn_start(self):
        """
        Prepares the next turn.
        """
        # Try to get blips to bud
        for blip in self.blips:
            if not blip.pregnant:
                self.try_to_get_pregnant(blip)

        # Restock food
        for x, y in self.food_tiles:
            self.map[y][x].value = min(self.map[y][x].value + params.FOOD_BUILD, params.FOOD_SIZE)

    def update(self):
        """
        Processes the actions of the blips.
        """
        states = {}
        for blip in self.blips.keys():
            states[blip] = self.build_state(blip)

        for blip in self.blips.keys():
            # Get blip action
            c = blip.decide_action(states[blip])

            # Execute action
            if c[0] == MOVE:
                self.move(blip, c[1])
            elif c[0] == STAY:
                self.stay(blip)
            elif c[0] == EAT:
                self.consume(blip, c[1])

    def turn_end(self):
        """
        End of turn calculations.
        """
        # Age blips
        for blip in self.blips.keys():
            blip.age += 1
            if blip.pregnant:
                blip.due_time += 1

        # Check for new blips or dead ones
        dead_blips = []
        due_blips = []
        for blip, pos in self.blips.items():
            # Kill off old  & weak blips
            if blip.age == blip.lifetime or blip.vapors <= 0 or blip.strength <= 0:
                dead_blips.append(blip)

            # Spawn new blip
            if blip.pregnant and blip.due_time == params.BUDDING_TIME:
                blip.pregnant = False
                blip.due_time = 0
                due_blips.append(blip)

        # Spawn babies
        for b in due_blips:
            self.spawn_blip(self.blips[b])

        # Remove dead blips
        for b in dead_blips:
            self.kill_blip(b)

    # Commands --------------------------------------------------------

    def move(self, blip, direction):
        """
        Moves the blip in the selected direction, updating
        its parameters and position. If the move is invalid
        the blip stay still.

        :param blip: Blip to be moved
        :param direction: Movement direction [NORTH, SOUTH, EAST, WEST]
        """
        if not direction:
            self.stay(blip)
            return

        dx, dy = DIRECTIONS[direction]
        x, y = self.blips[blip]
        new_pos = (x + dx, y + dy)

        # Only do the move if it's valid
        if not self.is_valid(new_pos):
            self.stay(blip)
            return

        # Update pos
        self.blips[blip] = new_pos
        self.map[y][x].blips.remove(blip)
        self.map[y + dy][x + dx].blips.append(blip)

        # Update params
        if blip.pregnant:
            factor = params.BUD_FACTOR
        else:
            factor = 1
        blip.strength -= factor * params.POWER_TO_MOVE
        blip.vapors -= factor * params.VAPOUR_TO_MOVE

    def stay(self, blip):
        """
        Causes a blip to pass the turn && updates its parameters.

        :param blip: The blip to update
        """
        if blip.pregnant:
            factor = params.BUD_FACTOR
        else:
            factor = 1
        blip.strength -= factor * params.POWER_TO_STAY
        blip.vapors -= factor * params.VAPOUR_TO_STAY

    def consume(self, blip, quantity):
        """
        The blip consumes min(quantity, available) resources.
        The blip remains stationary when consuming resources, so the
        stay penalties will be applied.

        :param blip: The blip that does the action
        :param quantity: Amount of resources to consume
        """
        x, y = self.blips[blip]

        # Consume resources for staying put
        self.stay(blip)

        # Drink water
        for _, (dx, dy) in DIRECTIONS.items():
            if (x + dx, y + dy) in self.water_tiles:
                blip.vapors += quantity

        # Consume the available food
        if self.map[y][x].value >= quantity:
            self.map[y][x].value -= quantity
            blip.strength += quantity
        else:
            blip.strength += self.map[y][x].value
            self.map[y][x].value = 0

    # Blip management -------------------------------------------------

    def spawn_blip(self, pos):
        """
        Spawns a new blip at the given position
        """
        x, y = pos

        # Compute the lifespan of the new blip
        scale = abs(y - self.height / 2) + abs(x - self.width / 2)
        scale /= (self.height + self.width) / 2
        lifespan = params.MAX_LIFE - random.randint(0, int(params.AGE_VAR * scale))

        # Create blip and place it on the map
        blip = Blip(lifespan)
        self.map[y][x].blips.append(blip)
        self.blips[blip] = pos

    def kill_blip(self, blip):
        """
        Removes a dead blip from the world.
        """
        if blip in self.blips:
            x, y = self.blips[blip]
            self.map[y][x].blips.remove(blip)
            del self.blips[blip]

    def try_to_get_pregnant(self, blip):
        """
        Tries to make the blip bud if all the requirements are met.
        """
        if blip.pregnant:
            return

        # Check if budding conditions are met
        if params.MIN_BUDDING_AGE <= blip.age <= params.MAX_BUDDING_AGE:
            if min(blip.strength, blip.vapors) >= params.BUDDING_MIN_RES:
                # Roll the dice
                accident = random.random() * 100 <= params.BUDDING_PROB
                if accident:
                    blip.pregnant = True
                    blip.due_time = 0

    # Blip states -----------------------------------------------------

    def build_state(self, blip):
        """
        Builds the current info for the blip

        :return: A tuple (available_directions, direction_to_water, direction_to_others)
        """
        available = [d for d, _ in self.get_neighbours(self.blips[blip])]
        in_forest = self.blips[blip] in self.food_tiles

        return available, self.sense_water(blip), self.sense_friends(blip), in_forest, self.sense_center(blip)

    def sense_center(self, blip):
        """
        Detects the shortest path to the map center.

        :param blip: The blip that makes the query
        :return: A direction from [NORTH, SOUTH, EAST, WEST]
        """
        x, y = self.blips[blip]
        center_x, center_y = (self.width / 2, self.height / 2)

        # Distance test
        dist = lambda pos: abs(pos[1] - center_y) + abs(pos[0] - center_x)

        # Choose the neighbour on the shortest path to center
        neighbours_dist = [(d, dist(pos)) for d, pos in self.get_neighbours((x, y))]
        return min(neighbours_dist, key=lambda t: t[1])[0]

    def sense_water(self, blip):
        """
        Detects the shortest path to the water, if the
        water is closer than SEE_RANGE.

        :param blip: The blip that makes the query
        :return: A direction from [NORTH, SOUTH, EAST, WEST],
                None if no blips are in range
        """
        x, y = self.blips[blip]

        # Check if water is in range
        if self.water_distance[y][x] > params.SEE_RANGE:
            return None

        # Return the direction to water
        # if a water tile is a neighbour
        for d, (dx, dy) in DIRECTIONS.items():
            if (x + dx, y + dy) in self.water_tiles:
                return d

        # Choose the neighbour on the shortest path to water
        neighbours_dist = [(d, self.water_distance[pos[1]][pos[0]]) for d, pos in self.get_neighbours((x, y))]
        return min(neighbours_dist, key=lambda t: t[1])[0]

    def sense_friends(self, blip):
        """
        Computes the direction that leads to the most blips.
        The other blips must be in SEE_RANGE

        :param blip: The blip that does the query
        :return: A direction from [NORTH, SOUTH, EAST, WEST],
                None if no blips are in range
        """
        x, y = self.blips[blip]

        # Get all the blips in SEE_RANGE
        range_test = lambda pos: 0 < abs(pos[1] - y) + abs(pos[0] - x) <= params.SEE_RANGE
        nearby_blips = list(filter(range_test, self.blips.values()))

        if not nearby_blips:
            return None

        # Retarded fix that exploits the fact that
        # there are no obstacles, except the water
        available_directions = {d: DIRECTIONS[d] for d, _ in self.get_neighbours((x, y))}
        directions = []
        for d, (dx, dy) in available_directions.items():
            reachable = list(filter(lambda pos: (pos[0] - x) * dx + (pos[1] - y) * dy >= 0, nearby_blips))
            directions.append((d, len(reachable)))

        return max(directions, key=lambda t: t[1])[0]

    # Helper methods --------------------------------------------------

    def is_valid(self, position):
        """
        Verifies if a position is contained in the grid and not a water tile.
        """
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height and self.map[y][x].type != WATER

    def compute_distances(self, start, costs=None):
        """
        Computes the distance from start to all the other points on the map.

        :param start:   A tuple (x, y) representing start point.
        :param costs:   An optional initial value for the costs array
        :return:    A 2D array of costs.
        """
        # Get starting points
        x, y = start

        # Init cost array
        if costs is None:
            costs = [[float('Inf') for _ in range(self.width)] for _ in range(self.height)]

        # Add start point to queue
        q = queue.Queue()
        costs[y][x] = 0
        q.put(start)

        while not q.empty():
            x, y = q.get()

            # Add neighbours to queue
            neighbours = [pos for d, pos in self.get_neighbours((x, y))]
            for nx, ny in neighbours:
                # Only add if we can update the cost
                if costs[ny][nx] > costs[y][x] + 1:
                    costs[ny][nx] = costs[y][x] + 1
                    q.put((nx, ny))

        return costs

    def get_neighbours(self, position):
        """
        Returns all the valid neighbouring tiles
        and the directions associated with them.

        :return: A list of tuples (direction, position)
        """
        x, y = position
        return [(d, (x + dx, y + dy)) for d, (dx, dy) in DIRECTIONS.items() if self.is_valid((x + dx, y + dy))]
