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

#os.system('')      # any call to os.system() is necessary for the renderer to work correctly
os.system('cls')    # windows only, os.system('clear') on linux

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

    def row_completed(self):
        self.points += 1000

class Board(): # TODO maybe extend numpy array?
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.array = np.zeros((height, width))
        self.block = Block(get_random_block_type(), self)
        self.gravity = RepeatedTimer(1, self.move, Direction.DOWN)
        self.score = Score()
        self.gameover = False

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
        for i in range(self.block.array.shape[0]):
            for j in range(self.block.array.shape[1]):
                self.array[y0 + i][x0 + j] += self.block.array[i][j]
            if not self.gameover and np.all(self.array[y0 + i] == 1):
                self.score.row_completed()
                self.remove_row(y0 + i)
        if not self.gameover:
            self.block = Block(get_random_block_type(), self)
            self.gravity.restart()

    def render(self):
        CURRENT_BLOCK_DISPLAY_HEIGHT = 6
        BOARD_DISPLAY_WIDTH = str(self.array[0]).__len__()
        BOARD_DISPLAY_HEIGHT = self.array.shape[0]
        GAME_INFO_DISPLAY_HEIGHT = CURRENT_BLOCK_DISPLAY_HEIGHT + 3     # initial line + score + input line

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

        # render current block
        block_display_vpadding = CURRENT_BLOCK_DISPLAY_HEIGHT - self.block.array.shape[0]
        block_display_hpadding = ceil(BOARD_DISPLAY_WIDTH/2) - self.block.array.shape[1]
        for i in range( floor(block_display_vpadding/2) ):
            result += " "*BOARD_DISPLAY_WIDTH + "\n"
        for i in range(self.block.array.shape[0]):
            result += " "*block_display_hpadding + str(self.block.array[i]) + " "*block_display_hpadding + "\n"
        for i in range( ceil(block_display_vpadding/2) ):
            result += " "*BOARD_DISPLAY_WIDTH + "\n"

        # render current board
        for i in range(display_array.shape[0]):
            result += str(display_array[i]) + "\n"

        # reposition cursor
        overwrite(result.count('\n') + 2)   # +2 for initial empty line and console input line
        print(result)
        
class Block: # TODO maybe extend numpy array?
    def __init__(self, array: np.ndarray, board: Board):
        self.array = array
        self.board = board
        self.board.block = self
        self.pos = [round(board.width/2)-round(self.array.shape[1]/2), 0]    # x,y

    def rotate(self):
        if self.board.gameover:
            return
        self.array = np.rot90(self.array)
        # move block back onto board if rotation moved parts of it out of bounds
        while self.array.shape[1]+self.pos[0] > self.board.width:
            self.pos[0] -= 1
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

    def detect_collision(self, direction):
        block = self.array
        x0 = self.pos[0]
        x1 = x0 + block.shape[1]
        y0 = self.pos[1]
        y1 = y0 + block.shape[0]

        match direction:
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

        overlap = block + self.board.array[y0:y1, x0:x1]
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
                case _:
                    None

    # Collect events until released
    with Listener( on_press=on_press, on_release=on_release ) as listener:
        listener.join()

    board.gravity.start()


if __name__ == '__main__':
    main()
