import pygame
import params
import argparse
import time
from world import World

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
OUTLINE = (191, 5, 191)
WATER = (25, 182, 193)

# Map size
GRID_SIZE = (50, 20)
BLOCK_SIZE = 30
LAKE_SIZE = 5
FOREST_WIDTH = 5


class BoardRenderer:
    """
    Handles the drawing & rendering of the game window.
    Displays the main grid of the game.
    """

    def __init__(self, name, grid_size, block_size):
        self.block_size = block_size
        self.grid_size = grid_size
        self.width, self.height = grid_size

        # Init pygame window
        pygame.init()
        pygame.display.set_caption(name)
        self.window = pygame.display.set_mode((self.width * block_size, self.height * block_size))

        # Init game fonts
        self.font = pygame.font.SysFont('comicsansms', 18)
        self.counter_font = pygame.font.SysFont('comicsansms', 36)

        # Create game board
        self.board = []
        for y in range(0, self.height):
            self.board.append([])
            for x in range(0, self.width):
                self.board[y].append(pygame.Rect(x * block_size, y * block_size, block_size, block_size))

        # Other params
        self.background_color = BLACK

    def draw_world(self, world):
        """
        Renders the game world as a grid of rectangles.
        Yellow rectangles -> blips
        Blue rectangle -> water
        Green rectangles -> forest

        :param world: The world simulation
        """

        # Clear screen
        self.window.fill(self.background_color)

        # Draw board
        for y in range(0, self.height):
            for x in range(0, self.width):
                c = BLACK

                blip_count = 0
                if world.map[y][x].blips:
                    blip_count = len(world.map[y][x].blips)

                    # Color code the blip's health %
                    total_status = (0, 0, 0)

                    for b in world.map[y][x].blips:
                        status = b.get_status()
                        total_status = tuple(map(sum, zip(total_status, status)))

                    # Get average health in case of multiple blips
                    hp = min(total_status)
                    c = (255, 255 * hp / blip_count, 0)

                elif world.map[y][x].type == "water":
                    c = WATER
                elif world.map[y][x].type == "forest":
                    # Make sure the tile doesn't disappear completely
                    fill_percent = max(world.map[y][x].value / params.FOOD_SIZE, 0.2)
                    c = (0, 255 * fill_percent, 0)

                pygame.draw.rect(self.window, c, self.board[y][x], 0)

                # Add count for multiple blips in a tile
                if blip_count > 1:
                    self.add_text(str(blip_count), BLACK, self.board[y][x].center, self.font)

        # Draw grid lines
        for i in range(0, self.height):
            screen_y = i * self.block_size
            pygame.draw.line(self.window, OUTLINE, (0, screen_y), (self.width * self.block_size, screen_y), 2)
        for i in range(0, self.width):
            screen_x = i * self.block_size
            pygame.draw.line(self.window, OUTLINE, (screen_x, 0), (screen_x, self.height * self.block_size), 2)

        # Write population count
        pos = (self.width * self.block_size / 2, 20)
        self.add_text(str(len(world.blips.keys())), WHITE, pos, self.counter_font)

        # Render to screen
        pygame.display.flip()

    def add_text(self, text, color, pos, font):
        """
        Add text on the screen centered on the given position.
        Does not update the display!

        :param text: Text to write on screen
        :param color: Text color to render
        :param pos: Text position on screen
        :param font: The font used to write the text
        """
        text = font.render(text, True, color)
        text_rec = text.get_rect(center=pos)
        self.window.blit(text, text_rec)


def init_game():
    """
    Creates a new BoardRenderer to display the game and
    a new World to simulate the game.

    :return: A tuple (BoardRenderer, Word)
    """
    return BoardRenderer('LifeSim', GRID_SIZE, BLOCK_SIZE), World(GRID_SIZE, LAKE_SIZE, FOREST_WIDTH)


def main():
    # Add arg types
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--simple", help="Don't display graphics", action="store_true")
    parser.add_argument("-d", "--delay", help="Delay between turns", type=float)
    parser.add_argument("-p", "--parameters_file", help="Load parameters from the given file")

    # Parse args
    args = parser.parse_args()

    delay = 0
    if args.delay:
        delay = args.delay

    if args.parameters_file:
        params.read_params(args.parameters_file)

    # Start the game
    renderer, world = init_game()

    turn = 0
    population = [0 for _ in range(params.MAX_LIFE)]
    done = False
    while not done:
        # Get input
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                    done = True

        # Prepare the next turn
        world.turn_start()

        # Update the world
        world.update()

        # Complete the current turn
        world.turn_end()

        # Draw world
        if not args.simple:
            renderer.draw_world(world)

        # Update population buffer
        current = len(world.blips.keys())
        population[turn % params.MAX_LIFE] = current
        if turn >= params.MAX_LIFE - 1:
            # Compute statistic for the period
            avg = sum(population) / len(population)
            best = max(population)
            worst = min(population)

            # Check if population has stabilized
            eps = 0.1 * avg
            if abs(best - avg) < eps and abs(worst - avg) < eps:
                done = True

            # Print some results in the terminal
            print("Best: {0}; Worst: {1}, Avg: {2}, Current {3}".format(best, worst, avg, current))

        turn += 1
        if current == 0:
            done = True

        # Time between rounds
        time.sleep(delay)

    pygame.quit()


if __name__ == "__main__":
    main()
