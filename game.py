import pygame
import params
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

        # Init game font
        self.font = pygame.font.SysFont('comicsansms', 18)

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
                pos = (x, y)
                c = BLACK

                blip_count = 0
                if world.map[y][x].blips:
                    blip_count = len(world.map[y][x].blips)

                    total_age = 0
                    for b in world.map[y][x].blips:
                        total_age += b.age

                    c = (255, 255, 0)

                elif world.map[y][x].type == "water":
                    c = WATER
                elif world.map[y][x].type == "food":
                    c = (0, 255 * world.map[y][x].value / params.FOOD_SIZE, 0)

                pygame.draw.rect(self.window, c, self.board[y][x], 0)

                # Add count for multiple blips in a tile
                if blip_count > 1:
                    self.add_text(str(blip_count), BLACK, self.board[y][x].center)

        # Draw grid lines
        for i in range(0, self.height):
            screen_y = i * self.block_size
            pygame.draw.line(self.window, OUTLINE, (0, screen_y), (self.width * self.block_size, screen_y), 2)
        for i in range(0, self.width):
            screen_x = i * self.block_size
            pygame.draw.line(self.window, OUTLINE, (screen_x, 0), (screen_x, self.height * self.block_size), 2)

        # Render to screen
        pygame.display.flip()

    def add_text(self, text, color, pos):
        """
        Add text on the screen centered on the given position.
        Does not update the display!

        :param text: Text to write on screen
        :param color: Text color to render
        :param pos: Text position on screen
        """
        text = self.font.render(text, True, color)
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
    # if len(sys.argv) < 2:
    #     print("Usage: python3 game.py settings_file")
    #     exit

    renderer, world = init_game()

    done = False
    while not done:
        # Get input
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                    pygame.quit()
                    done = True

        # Prepare the next turn
        world.turn_start()

        # Update the world
        world.update()

        # Complete the current turn
        world.turn_end()

        # Draw world
        renderer.draw_world(world)

        time.sleep(1)


if __name__ == "__main__":
    main()
