import copy
import unittest
import pytris
import numpy as np

def generate_random_board(width, height):
    return np.random.randint(0,2,(height,width))

class TestBoard(unittest.TestCase):
    pytris.Board.render = lambda self: None  # disable renderer
    def test_constructor_negative_dimensions(self):
        """
        Test negative dimensions for Board
        """
        self.assertRaises(ValueError, pytris.Board, -1, 10)
        self.assertRaises(ValueError, pytris.Board, 10, -1)
        self.assertRaises(ValueError, pytris.Board, -1, -1)

    def test_constructor_types_dimensions(self):
        """
        Test invalid types as dimensions for Board
        """
        self.assertRaises(TypeError, pytris.Board, 'test', 10)
        self.assertRaises(TypeError, pytris.Board, True, 10)
        self.assertRaises(TypeError, pytris.Board, 10.5, 10)
        self.assertRaises(TypeError, pytris.Board, 10, 'test')
        self.assertRaises(TypeError, pytris.Board, 10, True)
        self.assertRaises(TypeError, pytris.Board, 10, 10.5)
    
    def test_constructor(self):
        """
        Test Board constructor
        """
        def asserts(board: pytris.Board):
            self.assertIsInstance(board.width, int)
            self.assertIsInstance(board.height, int)
            self.assertIsInstance(board.array, pytris.np.ndarray)
            self.assertIsInstance(board.block_next, pytris.Block)
            self.assertIsInstance(board.gravity, pytris.RepeatedTimer)
            self.assertIsInstance(board.score, pytris.Score)

        # empty width
        board = pytris.Board(height = 10)
        self.assertIsInstance(board, pytris.Board)
        asserts(board)
        self.assertGreater(board.width, 0)
        self.assertEqual(board.height, 10)

        # empty height
        board = pytris.Board(width = 15)
        self.assertIsInstance(board, pytris.Board)
        asserts(board)
        self.assertEqual(board.width, 15)
        self.assertGreater(board.height, 0)

        # given width and height
        board = pytris.Board(15, 10)
        asserts(board)
        self.assertIsInstance(board, pytris.Board)
        self.assertEqual(board.width, 15)
        self.assertEqual(board.height, 10)

        # empty width and height
        board = pytris.Board()
        self.assertIsInstance(board, pytris.Board)
        asserts(board)
        self.assertGreater(board.width, 0)
        self.assertGreater(board.height, 0)

    def test_start_pause_resume(self):
        """
        Test start, pause and resume methods
        """
        board = pytris.Board()
        board.start()
        self.assertFalse(board.pause_renderer)
        self.assertFalse(board.gameover)
        self.assertTrue(board.gravity.state is pytris.RepeatedTimer.State.RUNNING)
        board.pause()
        self.assertTrue(board.pause_renderer)
        self.assertFalse(board.gameover)
        self.assertTrue(board.gravity.state is pytris.RepeatedTimer.State.STOPPED)
        board.resume()
        self.assertFalse(board.pause_renderer)
        self.assertFalse(board.gameover)
        self.assertTrue(board.gravity.state is pytris.RepeatedTimer.State.RUNNING)
        board.pause() # so gravity doesn't hang the test

    def test_drop_row_dimension(self):
        """
        Test if dropping a row keeps board dimensions
        """
        board = pytris.Board()
        initial_height = board.height
        initial_width = board.width

        def asserts():
            self.assertEqual(board.width, initial_width)  # board height must not change
            self.assertEqual(board.height, initial_height)  # board width must not change

        # drop bottom row
        board.drop_row(board.height-1)
        asserts()
        # drop bottom row using negative indices
        board.drop_row(-1)
        asserts()
        # drop first row
        board.drop_row(0)
        asserts()
        # drop inbetween row
        board.drop_row(2)
        asserts()
        # drop out of bounds row
        self.assertRaises(IndexError, board.drop_row, board.height)

    def test_drop_row(self):
        """
        Test if dropping a row removes the row and "pulls down" the rows above
        """
        board = pytris.Board()

        # fill board with randomly filled rows
        board.array = generate_random_board(board.height,board.width)
        array_initial = np.copy(board.array)
        
        board.drop_row(-1)  # drop bottom row

        self.assertTrue(np.all(board.array[0] == 0))    # top row must be empty
        for i in range(1, board.height-1):
            self.assertTrue(np.array_equal(board.array[i], array_initial[i-1]))   # every row after the first must be equal to the one previously above it



if __name__ == '__main__':
    unittest.main()