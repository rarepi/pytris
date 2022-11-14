#from PIL import Image
from math import ceil, floor
import numpy as np
from enum import Enum
from pynput.keyboard import Key, KeyCode, Listener
import os
from .RepeatedTimer import RepeatedTimer
from random import choice

MAX_BOARD_WIDTH = 50
MAX_BOARD_HEIGHT = 50
MIN_BOARD_DIMENSION: int # defined dynamically using Block_Type dict values
DEFAULT_BOARD_WIDTH = 10
DEFAULT_BOARD_HEIGHT = 20
INITIAL_SPEED = 1
MAX_SPEED = 3

def console_clear():
    """
    Clears the console
    """
    if os.name == 'nt': # windows
        os.system('cls')
    elif os.name == 'posix': # unix
        os.system('clear')

def console_overwrite(lines: int):
    """
    Shifts the console cursor up the given amount of lines

    * lines: the amount of lines to shift up
    """
    print("\x1B[" + str(lines) + "F")

class Direction(Enum):
    """
    Indicates one of four directions
    """
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

# Types of Tetris blocks - Might turn these into Block subclasses if it turns out to be beneficial
Block_Type = {
    "I": np.array([[1, 1, 1, 1]]),
    "J": np.array([[1, 0, 0], [1, 1, 1]]),
    "L": np.array([[0, 0, 1], [1, 1, 1]]),
    "O": np.array([[1, 1], [1, 1]]),
    "S": np.array([[0, 1, 1], [1, 1, 0]]),
    "T": np.array([[0, 1, 0], [1, 1, 1]]),
    "Z": np.array([[1, 1, 0], [0, 1, 1]])
}
# calculate minimum board dimension by determining the largest block dimension
MIN_BOARD_DIMENSION = max([max(x.shape[0], x.shape[1]) for x in Block_Type.values()])
if MIN_BOARD_DIMENSION > MAX_BOARD_WIDTH or MIN_BOARD_DIMENSION > MAX_BOARD_HEIGHT:
    raise ValueError("Failed to determine valid game board sizes. Make sure your terminal can display the estimated minimum character dimensions of {0}x{0}".format(MIN_BOARD_DIMENSION))

def get_random_block_type():
    """
    Returns a randomly chosen numpy array representing the form of a Tetris block
    """
    return choice(list(Block_Type.values()))

class Score():
    """
    Tracks the current play score of the player
    """
    def __init__(self):
        self.points = 0
        """ The current amount of points scored """
        self.scoring = {
            1: 40,
            2: 100,
            3: 300,
            4: 1200
        }
        """ Maps completed rows of blocks to the amount of points rewarded for doing so """

    def rows_completed(self, amount: int) -> int:
        """
        Increments the score according to the rows completed at once

        * amount: The amount of rows completed at once

        Returns the amount of points rewarded
        """
        if amount in self.scoring: # TODO: implement higher amount of rows (currently impossible to occur due to biggest block height being 4)
            self.points += self.scoring[amount]
            return self.scoring[amount]
        return 0

class Board():
    """
    Represents the play board. Tracks the game's metadata.
    """

    @property
    def height(self):
        return self.array.shape[0]

    @property
    def width(self):
        return self.array.shape[1]

    @property
    def block(self):
        """ The currently active block """
        return self._block

    @block.setter
    def block(self, block: 'Block'):
        self._block = block
        self.apply_gravity()

    @property
    def gameover(self) -> bool:
        """ If true, the game ends and game input methods will not execute. """
        return self._gameover

    @gameover.setter
    def gameover(self, gameover: bool):
        self._gameover = gameover
        self.render() # makes sure the renderer is executed at least one more time when gameover is updated

    def __init__(self, width = DEFAULT_BOARD_WIDTH, height = DEFAULT_BOARD_HEIGHT):
        if not (type(width) is int and type(height) is int):
            raise TypeError("Invalid Board dimensions: {} {}".format(width, height))
        if width < MIN_BOARD_DIMENSION or height < MIN_BOARD_DIMENSION:
            raise ValueError("Invalid Board dimensions: {0}, {1}\nMinimum values are: {2}, {2}".format(width, height, MIN_BOARD_DIMENSION))
        if width > MAX_BOARD_WIDTH or height > MAX_BOARD_HEIGHT:
            raise ValueError("Invalid Board dimensions: {}, {}\nMaximum values are: {}, {}".format(width, height, MAX_BOARD_WIDTH, MAX_BOARD_HEIGHT))
            
        self.array = np.zeros((height, width))
        """ A numpy array representing the play board itself. 0s are empty blocks, 1s are permanent blocks. Any other value is invalid and result in a gameover. """
        self.score = Score()
        """ The current score """
        self.block = Block(get_random_block_type(), self)
        self.block_next = Block(get_random_block_type(), self)
        """ The upcoming and currently inactive block """
        self.pause_renderer = True
        """ If true, the renderer will not execute """
        self.gameover = False

    def start(self):
        """
        Starts the game
        """
        self.pause_renderer = False
        self.render()
        self.block.unfreeze()

    def pause(self):
        """
        Pauses the game
        """
        self.pause_renderer = True
        self.block.freeze()

    def resume(self):
        """
        Resumes the game after being paused
        """
        self.start()

    def apply_gravity(self) -> float:
        """
        Applies gravity to the current block. The gravity is weighted by the current score points.

        Returns the applied gravity.
        """
        g = INITIAL_SPEED + self.score.points * 0.00033
        if g > MAX_SPEED:
            g = MAX_SPEED
        self.block.gravity = g
        return g

    def drop_row(self, idx: int):
        """
        Removes the given row from the board while maintaining the board's dimensions

        * idx: The index of the row, top to bottom
        """
        self.array = np.delete(self.array, idx, 0) # remove row
        self.array = np.insert(self.array, 0, 0, 0) # add empty row at the top

    def finish_completed_rows(self, start: int, stop: int) -> int:
        """
        Removes any completed block rows in the given index range and attributes points to the player according to the amount of rows completed.

        * start: The index of the first row to be checked for completion (inclusive start index)
        * stop: The amount of consecutive rows to be checked for completion (exlusive end index)

        Returns the amount of completed rows found
        """
        rows_completed = 0
        for i in range(start, stop):
            if not self.gameover and np.all(self.array[i] == 1):
                self.drop_row(i)
                rows_completed += 1
        if rows_completed > 0:
            self.score.rows_completed(rows_completed)
            self.apply_gravity()
        return rows_completed

    def render(self):
        """
        Prints the current state of the board to the console, including the current play block and its metadata.
        """
        if self.pause_renderer:
            return

        def format_array_str(array: np.ndarray) -> str:
            """
            Builds and returns a stylized string of a numpy array.
            """
            char_replacements = {
                ".": "",
                " ": "",
                "0": " ",
                "1": "X",
                "[": "|",
                "]": "|",
                "2": "#",
                "3": "#",
                "4": "#"
            }
            result = str(array)
            for key in char_replacements:
                result = result.replace(key, char_replacements[key])
            return result
            
        CURRENT_BLOCK_DISPLAY_HEIGHT = 6
        BOARD_DISPLAY_WIDTH = format_array_str(self.array[0]).__len__()

        result = ""

        # add player's block to displayed board
        display_array = np.copy(self.array)
        x0 = self.block.pos[0]
        y0 = self.block.pos[1]
        for i in range(self.block.height):
            for j in range(self.block.width):
                display_array[y0 + i][x0 + j] += self.block.array[i][j]

        # render game info
        if self.gameover:
            result += "### GAME OVER ###\n"
        result += "Score: " + str(self.score.points) + "\n"
        result += "Speed: " + "%.2f" % self.block.gravity + " bps\n"

        # render upcoming block
        block_display_vpadding = CURRENT_BLOCK_DISPLAY_HEIGHT - self.block_next.height
        block_display_hpadding = ceil(BOARD_DISPLAY_WIDTH/2) - self.block_next.width
        for i in range( floor(block_display_vpadding/2) ):
            result += " "*BOARD_DISPLAY_WIDTH + "\n"
        for i in range(self.block_next.height):
            result += " "*block_display_hpadding + format_array_str(self.block_next.array[i]) + " "*block_display_hpadding + "\n"
        for i in range( ceil(block_display_vpadding/2) ):
            result += " "*BOARD_DISPLAY_WIDTH + "\n"

        # render current board
        for i in range(display_array.shape[0]):
            result += format_array_str(display_array[i]) + "\n"

        # reposition cursor
        console_overwrite(result.count('\n') + 2)   # +2 for initial empty line and console input line
        print(result)
        
class Block:
    @property
    def height(self):
        """ The height of the block """
        return self.array.shape[0]

    @property
    def width(self):
        """ The width of the block """
        return self.array.shape[1]

    @property
    def board(self):
        """ The Board the block is associated with """
        return self._board

    @board.setter
    def board(self, board: Board):
        self._board = board

        # move block to starting position of board
        if self.board is not None:
            self.pos = [self.board.width//2 - self.width//2, 0]    # x,y
        else:
            self.pos = None

    @property
    def gravity(self) -> float:
        """
        The amount of gravity applied to the block. \\
        The block will move down (gravity) rows per second. Negative gravity moves the block up.
        """
        if self._gravity is None or self._gravity.interval <= 0:
            return 0

        if self._gravity.args[0] is Direction.DOWN:
            return (1 / self._gravity.interval)
        elif self._gravity.args[0] is Direction.UP:
            return (-1 / self._gravity.interval)
        else:
            raise ValueError("Unexpected gravity direction {}".format(self._gravity.args[0]))

    @gravity.setter
    def gravity(self, g: float):
        if g > 0:
            self._gravity = RepeatedTimer(1 / g, self.move, Direction.DOWN)
        elif g < 0:
            self._gravity = RepeatedTimer(-1 / g, self.move, Direction.UP)
        else:
            self._gravity = None

    def __init__(self, array: np.ndarray, board: Board):
        self.array = array
        """ A numpy array representing the block itself. 0s are empty, 1s filled. """
        self.board = board
        """ A numpy array representing the play board itself. 0s are empty blocks, 1s are permanent blocks. Any other value is invalid and result in a gameover. """
        self.pos: list[int, int]
        """ Current location of the block on the associated board """

    def freeze(self):
        """ Freezes the block by disabling its gravity """
        try:
            self._gravity.pause()
        except AttributeError:
            pass # no need to freeze if there is no gravity

    def unfreeze(self):
        """ Unfreezes the block by reenabling its gravity """
        try:
            self._gravity.resume()
        except AttributeError:
            pass # no need to unfreeze if there is no gravity

    def rotate(self):
        """ 
        Rotates the block by 90 degrees. \\
        If this rotation results in a block collision on the current board, it will attempt to move to the left or to the right. If this does not resolve the collision, the block will not rotate.

        This method does not execute after gameover.
        """
        if self.board.gameover:
            return

        # no need to check for collision if there is no board
        if self.board is None:
            self.array = np.rot90(self.array)
            return

        if not self.detect_collision(rotate = True):
            self.array = np.rot90(self.array)
        else:
            for direction in (Direction.RIGHT, Direction.LEFT):
                if not self.detect_collision(direction, True):
                    self.board.pause()  # don't progress the game while the block is rotated at an illegal location
                    self.array = np.rot90(self.array) # rotate block into illegal location
                    self.move(direction) # move block into legal location
                    self.board.resume()
                    break
        self.board.render() # immediately display the updated rotation

    def move(self, direction: Direction):
        """ 
        Moves the block into the given Direction if possible.\\
        Attempting to move a block down into an illegal location will instead finalize it in its current location.
            
        This method does not execute after gameover.
        """
        if self.board is None or self.board.gameover:
            return

        match direction:
            case Direction.UP:
                if not self.detect_collision(direction):
                    self.pos[1] = self.pos[1] - 1
            case Direction.RIGHT:
                if not self.detect_collision(direction):
                    self.pos[0] = self.pos[0] + 1
            case Direction.DOWN:
                if not self.detect_collision(direction):
                    self.pos[1] = self.pos[1] + 1
                else:
                    self.finalize()
            case Direction.LEFT:
                if not self.detect_collision(direction):
                    self.pos[0] = self.pos[0] - 1
        self.board.render()

    def finalize(self):
        """
        Writes the Block's data onto the board array at its current location.\\
        The upcoming Block will then be "spawned" and assigned as the current block.\\
        If there is no space to do so, gameover will be set and the upcoming block will be finalized to visualize the gameover cause.
        """
        if self.board is None:
            raise AttributeError("Cannot finalize block when no board is set.")

        if self.detect_collision():
            self.board.gameover = True
        self.freeze()
        x0 = self.pos[0]
        y0 = self.pos[1]
        # write block onto board
        for i in range(self.height):
            for j in range(self.width):
                self.board.array[y0 + i][x0 + j] += self.array[i][j]

        # check for completed rows
        self.board.finish_completed_rows(y0, y0 + self.height)

        # swap to next block
        if not self.board.gameover:
            if not self.board.block_next.detect_collision(None):
                self.board.block = self.board.block_next
                self.board.block_next = Block(get_random_block_type(), self.board)
                self.board.block.unfreeze()
            else: # next block is stuck already
                self.board.gameover = True
                self.board.block_next.finalize()

    def detect_collision(self, move_direction: Direction = None, rotate = False):
        """
        Returns True, if the Block overlaps with an area of the Board that may not be written on.\\
        This includes fields that have already been written on and areas that are out of bounds.

        * move_direction: If given, the collision check will be determined with a move in this Direction. Default is None.
        * rotate: If set to True, the collision check will be determined with a rotation by 90 degrees. Default is False.
        """
        if self.board is None:
            raise AttributeError("Cannot detect collision when no board is set.")

        if rotate:
            block_array = np.rot90(self.array)
        else:
            block_array = self.array

        x0 = self.pos[0]
        x1 = x0 + block_array.shape[1]
        y0 = self.pos[1]
        y1 = y0 + block_array.shape[0]

        match move_direction:
            case Direction.UP:
                y0 -= 1
                y1 -= 1
            case Direction.RIGHT:
                x0 += 1
                x1 += 1
            case Direction.DOWN:
                y0 += 1
                y1 += 1
            case Direction.LEFT:
                x0 -= 1
                x1 -= 1
            case _:
                pass

        if x0 < 0 or y0 < 0 or x1 > self.board.width or y1 > self.board.height:
            return True

        try:
            overlap = block_array + self.board.array[y0:y1, x0:x1]
            if np.any(overlap[:, :] > 1):
                return True
            else:
                return False
        except ValueError:
            return True

def main():
    #os.system('')      # any call to os.system() is necessary for the renderer to work correctly
    console_clear()             # includes os.system() call

    board = Board()

    def on_press(key):
        None

    def on_release(key: Key | KeyCode):
        if isinstance(key, Key):
            if key == Key.esc:
                board.pause()
                return False
        if isinstance(key, KeyCode):
            match key.char:
                case 'w':
                    pass
                case 'a':
                    board.block.move(Direction.LEFT)
                case 's':
                    board.block.move(Direction.DOWN)
                case 'd':
                    board.block.move(Direction.RIGHT)
                case 'r':
                    board.block.rotate()
                case 'c':
                    console_clear()
                    board.render()
                case _:
                    None

    board.start()

    # Collect events until released
    with Listener( on_press=on_press, on_release=on_release ) as listener:
        listener.join()
