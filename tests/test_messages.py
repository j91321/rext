# This file is part of REXT
# test_utils - unit test for interface.messages
# Author: Ján Trenčanský
# License: GNU GPL v3

import unittest
import unittest.mock
import interface.messages
import builtins


class MessagesTest(unittest.TestCase):

    # Test will work only under linux don't know why mocking interface.utils.identify_os screws things
    # @unittest.mock.patch("interface.utils.identify_os")
    @unittest.mock.patch("builtins.print", autospec=True)  # Don't use print in these tests
    def test_print_messages(self, mock_builtins):
        # mock_utils.return_value = "posix"
        test_string = "Hello World"
        interface.messages.print_success(test_string)
        mock_builtins.assert_called_with("\033[32m\033[1m[+]\033[0m", test_string)

        interface.messages.print_error(test_string)
        mock_builtins.assert_called_with("\033[91m\033[1m[-]\033[0m", test_string)

        interface.messages.print_warning(test_string)
        mock_builtins.assert_called_with("\033[93m\033[1m[!]\033[0m", test_string)

        interface.messages.print_failed(test_string)
        mock_builtins.assert_called_with("\033[91m\033[1m[-]\033[0m", test_string)

        interface.messages.print_help(test_string)
        mock_builtins.assert_called_with("\033[95m\033[1m[?]\033[0m", test_string)

        interface.messages.print_info(test_string)
        mock_builtins.assert_called_with("\033[94m\033[1m[*]\033[0m", test_string)

        interface.messages.print_green(test_string)
        mock_builtins.assert_called_with("\033[32m%s\033[0m" % test_string)

        interface.messages.print_red(test_string)
        mock_builtins.assert_called_with("\033[91m%s\033[0m" % test_string)

        interface.messages.print_blue(test_string)
        mock_builtins.assert_called_with("\033[94m%s\033[0m" % test_string)

        interface.messages.print_yellow(test_string)
        mock_builtins.assert_called_with("\033[93m%s\033[0m" % test_string)

        interface.messages.print_purple(test_string)
        mock_builtins.assert_called_with("\033[95m%s\033[0m" % test_string)


if __name__ == '__main__':
    unittest.main()
