# This file is part of REXT
# test_utils - unit test for core.loader
# Author: Ján Trenčanský
# License: GNU GPL v3

# import unittest
# import unittest.mock
# import core.loader
#
# TODO Tests are broken find a better way how to fix them
# class CmdUiTest(unittest.TestCase):
#
#     @unittest.mock.patch("core.loader.sqlite3")
#     def test_db_open(self, mock_sqlite):
#         path = "./databases/oui.db"
#         core.loader.open_database(path)
#         self.assertTrue(mock_sqlite.connect.assert_called_once_with(path))
#
#     def test_db_close(self):  # Some of these tests are so dumb, don't know why I even bother with them
#         connect = unittest.mock.MagicMock()
#         core.loader.close_database(connect)
#         self.assertTrue(connect.close.assert_called())
#     # Tests for load_module don't seem necessary and I haven't got a clue how to test delete_module()
#
#
# if __name__ == '__main__':
#     unittest.main()
