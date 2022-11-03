import unittest
import pytris
import os
import sys

class TestBoard(unittest.TestCase):
    pytris.Board.render = lambda self: None  # disable renderer
    def test_negative_dimensions(self):
        """
        Test negative dimensions for Board
        """
        self.assertRaises(ValueError, pytris.Board, -1, 10)
        self.assertRaises(ValueError, pytris.Board, 10, -1)
        self.assertRaises(ValueError, pytris.Board, -1, -1)

    def test_types_dimensions(self):
        """
        Test invalid types as dimensions for Board
        """
        self.assertRaises(TypeError, pytris.Board, 'test', 10)
        self.assertRaises(TypeError, pytris.Board, True, 10)
        self.assertRaises(TypeError, pytris.Board, 10.5, 10)
        self.assertRaises(TypeError, pytris.Board, 10, 'test')
        self.assertRaises(TypeError, pytris.Board, 10, True)
        self.assertRaises(TypeError, pytris.Board, 10, 10.5)
    
    def test_board_constructor(self):
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

    def test_board_start(self):
        """
        Test Board game start
        """
        board = pytris.Board()
        board.start()
        self.assertFalse(board.pause_renderer)
        self.assertFalse(board.gameover)
        board.pause()
        self.assertTrue(board.pause_renderer)
        self.assertFalse(board.gameover)
        board.resume()
        self.assertFalse(board.pause_renderer)
        self.assertFalse(board.gameover)
        board.pause() # so gravity doesn't hang the test

if __name__ == '__main__':
    unittest.main()