import random
import queue
import params

DIRECTIONS = {"North": (0, -1), "South": (0, 1), "West": (-1, 0), "East": (1, 0)}
AVAILABLE = 0
WATER = 1
FRIENDS = 2


class MapTile:
    def __init__(self):
        self.type = "normal"
        self.blips = []
        self.value = 0


class Blip:
    """
    An agent that takes part in the simulation.
    """

    def __init__(self, lifetime):
        self.lifetime = lifetime
        self.age = 0
        self.strength = params.MAX_RES
        self.vapours = params.MAX_RES
        self.pregnant = False
        self.due_time = 0

    def decide_action(self, state):
        if not state[WATER]:
            return "stand", None
        elif state[WATER] not in state[AVAILABLE]:
            return "consume", params.MAX_RES - self.vapours
        else:
            return "move", state[WATER]


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
                self.map[y][x].type = "food"
                self.food_tiles.append((x, y))

        # Create lake in the West
        lake_start = random.randint(0, self.height - lake_size)
        for y in range(lake_size):
            for x in range(lake_size):
                self.map[lake_start + y][x].type = "water"
                self.water_tiles.append((x, lake_start + y))

        # Init blips
        for i in range(params.INIT_POP):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)

            # Spawn only on free tiles
            while self.map[y][x].type != "normal":
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
            if c[0] == "move":
                self.move(blip, c[1])
            elif c[0] == "stay":
                self.stay(blip)
            elif c[0] == "consume":
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
        for blip, pos in self.blips.items():
            # Kill off old blip
            if blip.age == blip.lifetime:
                dead_blips.append(blip)

            # Spawn new blip
            # if blip.pregnant and blip.due_time == params.BUDDING_TIME:
            #     blip.pregnant = False
            #     blip.due_time = 0
            #     self.spawn_blip(pos)

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
        :param direction: Movement direction [North, South, East, West]
        """
        dx, dy = DIRECTIONS[direction]
        x, y = self.blips[blip]
        new_pos = (x + dx, y + dy)

        # Only do the move if it's valid
        if not self.is_valid(new_pos):
            self.stay(blip)

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
        blip.vapours -= factor * params.VAPOUR_TO_MOVE

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
        blip.vapours -= factor * params.VAPOUR_TO_STAY

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
        neighbours = [pos for _, pos in self.get_neighbours((x, y))]
        if any(map(lambda pos: self.map[pos[1]][pos[0]].type == "water", neighbours)):
            blip.vapours += quantity

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
        # TODO add scaling based on distance
        lifespan = params.MAX_LIFE - random.randint(0, params.AGE_VAR)

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
            if min(blip.strength, blip.vapours) >= params.BUDDING_MIN_RES:
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
        return available, self.sense_water(blip), self.sense_friends(blip)

    def sense_water(self, blip):
        """
        Detects the shortest path to the water, if the
        water is closer than SEE_RANGE.

        :param blip: The blip that makes the query
        :return: A direction from [North, South, East, West],
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
        :return: A direction from [North, South, East, West],
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
        return 0 <= x < self.width and 0 <= y < self.height and self.map[y][x].type != "water"

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
