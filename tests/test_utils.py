# This file is part of REXT
# test_utils - unit test for interface.utils
# Author: Ján Trenčanský
# License: GNU GPL v3

import unittest
import unittest.mock
import interface.utils


class UtilsTest(unittest.TestCase):
    mac_values_good = ("00:11:22:33:44:55",
                       "00-11-22-33-44-55",
                       "001122334455")
    mac_values_bad = ("00/11/22/33/44/55",
                      "00:11:22:33:44:55:66",
                      "00:11,",
                      "00-11-22-GG-44-55",
                      "adklsajflskd"
                      "165460")

    def test_validate_mac_good_values(self):
        """validate_mac() should True if mac with either : - or nothing as delimeter"""
        for value in self.mac_values_good:
            result = interface.utils.validate_mac(value)
            self.assertTrue(result)

    def test_validate_mac_bad_values(self):
        """validate_mac() should return False if invalid mac is input"""
        for value in self.mac_values_bad:
            result = interface.utils.validate_mac(value)
            self.assertFalse(result)

    ip_values_good = ("192.168.1.1",
                      "65.32.128.55")
    ip_values_bad = ("192.168.1.1.",
                     "192.168.1.256",
                     "192.168.256.1",
                     "192.-1.111.13",
                     "192.A.13.22",
                     "sfdsfsdf")

    def test_validate_ipv4_good_values(self):
        """True if valid IPv4"""
        for value in self.ip_values_good:
            result = interface.utils.validate_ipv4(value)
            self.assertTrue(result)

    def test_validate_ipv4_bad_values(self):
        """False if invalid IPv4"""
        for value in self.ip_values_bad:
            result = interface.utils.validate_ipv4(value)
            self.assertFalse(result)

    @unittest.mock.patch("interface.utils.os")
    def test_file_exists(self, mock_os):
        """return true if file exists"""
        mock_os.path.isfile.return_value = True
        result = interface.utils.file_exists("./core/Exploit.py")

        mock_os.path.isfile.assert_called_with("./core/Exploit.py")
        self.assertTrue(result)

        mock_os.path.isfile.return_value = False
        result = interface.utils.file_exists("./core/Exploit.py")
        self.assertFalse(result)

    def test_make_import_name(self):
        """make_import_name() should return valid name for loader.py to import"""
        string = "exploits/zte/somemodule"
        result = interface.utils.make_import_name(string)
        self.assertEqual("modules.exploits.zte.somemodule", result)

    @unittest.mock.patch("interface.utils.os")
    def test_identify_os(self, mock_os):
        """identify_os() should call os.name and return it's value"""
        # Another useless test
        # anyway these are just simple tests so I can get hang of writing them
        mock_os.name = "posix"
        interface.utils.identify_os()
        self.assertEqual("posix", mock_os.name)

    @unittest.mock.patch("interface.utils.os")
    def test_list_dirs(self, mock_os):
        """list_dirs() returns list of dirs in path, remove __pychache__ and .cache"""
        path = "./"
        # I should probably mock .join here but it's not that important I think
        mock_os.listdir.return_value = ("decryptors", "exploits",
                                        "misc", "__pycache__",
                                        ".cache", "__init__.py")
        # Side effect is a list of return values as isdir() is being called
        mock_os.path.isdir.side_effect = [True, True, True, True, True, False]
        result = interface.utils.list_dirs(path)
        self.assertEqual(result, {"decryptors", "exploits", "misc"})

    @unittest.mock.patch("interface.utils.os")
    def test_list_files(self, mock_os):
        """list_files() returns files in path no extension, remove __init__.py"""
        path = "./modules/exploits/dlink"
        mock_os.listdir.return_value = ("dir300.py", "dir600.py", "__init__.py", "__pycache__")
        mock_os.path.isfile.side_effect = [True, True, True, False]
        mock_os.path.splitext.side_effect = [("dir300", "py"), ("dir600", "py"), ("__init__", "py")]
        result = interface.utils.list_files(path)
        self.assertEqual(result, {"dir300", "dir600"})

    # Don't know how to mock DB cursor, I'm missing something
    # @unittest.mock.patch("interface.utils.core.globals.ouidb_conn")
    # def test_lookup_mac(self, mock_core_globals):
    #     """lookup_mac() should return manufacturer name based on OUI"""
    #     mac = "00:11:22:33:44:55"
    #     mock_core_globals.cursor().return_value = unittest.mock.MagicMock()
    #     mock_core_globals.execute().return_value = None
    #     mock_core_globals.fetchone().return_value = "Cisco"
    #     result = interface.utils.lookup_mac(mac)
    #     self.assertEqual(result, "(Cisco)")
    #
    #     mock_core_globals.cursor.fetchone.return_value = None
    #     result = interface.utils.lookup_mac(mac)
    #     self.assertEqual(result, "(Unknown)")


if __name__ == '__main__':
    unittest.main()
