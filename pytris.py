#from PIL import Image
from math import ceil, floor
import numpy as np
from enum import Enum
from pynput.keyboard import Key, KeyCode, Listener
import os
from RepeatedTimer import RepeatedTimer
from random import choice

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
INITIAL_SPEED = 1
MAX_SPEED = 3


clear = lambda: os.system('cls')    # windows only, os.system('clear') on linux
clear()
#os.system('')      # any call to os.system() is necessary for the renderer to work correctly

def overwrite(lines):
    print("\x1B[" + str(lines) + "F")

class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

Block_Type = {
    "I": np.array([[1, 1, 1, 1]]),
    "J": np.array([[1, 0, 0], [1, 1, 1]]),
    "L": np.array([[0, 0, 1], [1, 1, 1]]),
    "O": np.array([[1, 1], [1, 1]]),
    "S": np.array([[0, 1, 1], [1, 1, 0]]),
    "T": np.array([[0, 1, 0], [1, 1, 1]]),
    "Z": np.array([[1, 1, 0], [0, 1, 1]])
}

def get_random_block_type():
    return choice(list(Block_Type.values()))

class Score():
    def __init__(self):
        self.points = 0
        self.scoring = {
            1: 40,
            2: 100,
            3: 300,
            4: 1200
        }

    def rows_completed(self, amount):
        if amount in self.scoring:
            self.points += self.scoring[amount]

class Board(): # TODO maybe extend numpy array?
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.array = np.zeros((height, width))
        self.block = Block(get_random_block_type(), self)
        self.block_next = Block(get_random_block_type(), self)
        self.gameover = False
        self.score = Score()
        self.set_gravity(INITIAL_SPEED)
        self.pause_renderer = False

    def set_gravity(self, g):
        if g > MAX_SPEED:
            g = MAX_SPEED
        self.gravity = RepeatedTimer(1 / g, self.move, Direction.DOWN)

    def move(self, direction):
        self.block.move(direction)

    def remove_row(self, idx):
        self.array = np.delete(self.array, idx, 0) # remove row
        self.array = np.insert(self.array, 0, 0, 0) # add empty row at the top
        return

    def finalize_block(self):
        if self.block.detect_collision(None):
            self.gameover = True

        self.gravity.stop()
        x0 = self.block.pos[0]
        y0 = self.block.pos[1]
        # write block onto board
        for i in range(self.block.array.shape[0]):
            for j in range(self.block.array.shape[1]):
                self.array[y0 + i][x0 + j] += self.block.array[i][j]

        # another vertical loop to check for finished rows
        rows_completed = 0
        for i in range(self.block.array.shape[0]):
            if not self.gameover and np.all(self.array[y0 + i] == 1):
                self.remove_row(y0 + i)
                rows_completed += 1
        if rows_completed > 0:
            self.score.rows_completed(rows_completed)
            self.set_gravity(INITIAL_SPEED + self.score.points * 0.00033)

        if not self.gameover:
            self.block = self.block_next
            self.block_next = Block(get_random_block_type(), self)
            # check if new block is stuck already
            if self.block.detect_collision(None):
                self.finalize_block()
            self.gravity.restart()

    def render(self):
        if self.pause_renderer:
            return

        def format_array_str(array):
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

        # temporarily add player's block to board
        display_array = np.copy(self.array)
        x0 = self.block.pos[0]
        y0 = self.block.pos[1]
        for i in range(self.block.array.shape[0]):
            for j in range(self.block.array.shape[1]):
                display_array[y0 + i][x0 + j] += self.block.array[i][j]

        # render game info
        if self.gameover:
            result += "### GAME OVER ###\n"
        result += "Score: " + str(self.score.points) + "\n"
        result += "Speed: " + "%.2f" % (1 / self.gravity.interval) + " bps\n"

        # render upcoming block
        block_display_vpadding = CURRENT_BLOCK_DISPLAY_HEIGHT - self.block_next.array.shape[0]
        block_display_hpadding = ceil(BOARD_DISPLAY_WIDTH/2) - self.block_next.array.shape[1]
        for i in range( floor(block_display_vpadding/2) ):
            result += " "*BOARD_DISPLAY_WIDTH + "\n"
        for i in range(self.block_next.array.shape[0]):
            result += " "*block_display_hpadding + format_array_str(self.block_next.array[i]) + " "*block_display_hpadding + "\n"
        for i in range( ceil(block_display_vpadding/2) ):
            result += " "*BOARD_DISPLAY_WIDTH + "\n"

        # render current board
        for i in range(display_array.shape[0]):
            result += format_array_str(display_array[i]) + "\n"

        # reposition cursor
        overwrite(result.count('\n') + 2)   # +2 for initial empty line and console input line
        print(result)
        
class Block: # TODO maybe extend numpy array?
    def __init__(self, array: np.ndarray, board: Board):
        self.array = array
        self.board = board
        self.pos = [round(board.width/2)-round(self.array.shape[1]/2), 0]    # x,y

    def rotate(self):
        if self.board.gameover:
            return
        if not self.detect_collision(None, True):
            self.array = np.rot90(self.array)
        else:
            for direction in Direction:
                if not self.detect_collision(direction, True):
                    self.board.pause_renderer = True
                    self.array = np.rot90(self.array)
                    self.move(direction)
                    self.board.pause_renderer = False
                    break
        self.board.render()

    def move(self, direction):
        if self.board.gameover:
            return

        match direction:
            case Direction.UP:
                return # not a valid Tetris move
            case Direction.RIGHT:
                if self.pos[0] + self.array.shape[1] < self.board.width and not self.detect_collision(direction):
                    self.pos[0] = self.pos[0] + 1
            case Direction.DOWN:
                if self.pos[1] + self.array.shape[0] < self.board.height and not self.detect_collision(direction):
                    self.pos[1] = self.pos[1] + 1
                else:
                    self.board.finalize_block()
            case Direction.LEFT:
                if self.pos[0] > 0 and not self.detect_collision(direction):
                    self.pos[0] = self.pos[0] - 1
        self.board.render()

    def detect_collision(self, move_direction, rotate = False):
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
                None

        if x1 > self.board.array.shape[1] or y1 > self.board.array.shape[0]:
            return True

        try:
            overlap = block_array + self.board.array[y0:y1, x0:x1]
        except ValueError:
            return True

        if np.any(overlap[:, :] > 1):
            return True
        else:
            return False

def main():
    board = Board(BOARD_WIDTH, BOARD_HEIGHT)

    def on_press(key):
        None

    def on_release(key: Key | KeyCode):
        if isinstance(key, Key):
            if key == Key.esc:
                board.gravity.stop()
                return False
        if isinstance(key, KeyCode):
            match key.char:
                case 'w':
                    board.block.move(Direction.UP)
                case 'a':
                    board.block.move(Direction.LEFT)
                case 's':
                    board.block.move(Direction.DOWN)
                case 'd':
                    board.block.move(Direction.RIGHT)
                case 'r':
                    board.block.rotate()
                case 'c':
                    clear()
                    board.render()
                case _:
                    None

    # Collect events until released
    with Listener( on_press=on_press, on_release=on_release ) as listener:
        listener.join()

    board.gravity.start()


if __name__ == '__main__':
    main()
