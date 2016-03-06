# This file is part of REXT
# test_utils - unit test for interface.cmdui
# Author: Ján Trenčanský
# License: GNU GPL v3

import io
import sys
import unittest
import core.globals
import unittest.mock
import interface.cmdui


# http://stackoverflow.com/questions/30056986/create-automated-tests-for-interactive-shell-based-on-pythons-cmd-module
class CmdUiTest(unittest.TestCase):
    def setUp(self):
        self.mock_stdout = unittest.mock.create_autospec(sys.stdout)

    def create(self):
        return interface.cmdui.Interpreter(stdout=self.mock_stdout)

    # Not really working don't know why, nobody seems to know
    # Workaround: mock sys.stdout with StringIO (like banner)
    # http://stackoverflow.com/questions/34500249/writing-unittest-for-python3-shell-based-on-cmd-module
    def _last_write(self, nr=None):
        """:return: last `n` output lines"""
        if nr is None:
            return self.mock_stdout.write.call_args[0][0]
        # It looks like cmd module bypasses .write()
        # self.assertTrue(self.mock_stdout.write.called_with) always returns False
        return "".join(map(lambda c: c[0][0], self.mock_stdout.write.call_args_list[-nr:]))

    @unittest.mock.patch("interface.cmdui.loader")
    @unittest.mock.patch("interface.cmdui.interface.utils")
    def test_show_command_dirs(self, mock_loader, mock_utils):
        mock_loader.check_dependencies.return_value = None
        mock_loader.open_database.return_value = None
        # mock_utils.list_dirs.side_effect = (("exploits"), ("dlink", "linksys", "zte"))
        # mock_utils.lst_files.return_value = {"mod1", "mod2"}

        fake_banner = io.StringIO("Yey banner.txt")
        # Mocking banner and DB that are used on Interpreter() init are not that important
        with unittest.mock.patch('interface.cmdui.open', return_value=fake_banner, create=True):
            cli = self.create()
            cli.active_module = {'harvesters': {'airlive': {'WT2000ARM'}},
                                 'exploits': {'netgear': {'wndr_auth_bypass', 'n300_auth_bypass'},
                                              'zyxel': {'rom-0'},
                                              'zte': {'f660_config_download'},
                                              'linksys': {'ea6100_auth_bypass'},
                                              'dlink': {'dir890l_soapaction', 'dir300_600_exec'}}}
            with unittest.mock.patch('sys.stdout', new=io.StringIO()) as mock_stdout:
                self.assertFalse(cli.onecmd("show"))
            self.assertEqual("""exploits\nharvesters""", mock_stdout.getvalue().strip())

    @unittest.mock.patch("interface.cmdui.loader")
    @unittest.mock.patch("interface.cmdui.interface.utils")
    def test_show_command_files(self, mock_loader, mock_utils):
        mock_loader.check_dependencies.return_value = None
        mock_loader.open_database.return_value = None
        # mock_utils.list_dirs.side_effect = (("exploits"), ("dlink", "linksys", "zte"))
        # mock_utils.lst_files.return_value = {"mod1", "mod2"}

        fake_banner = io.StringIO("Yey banner.txt")
        # Mocking banner and DB that are used on Interpreter() init are not that important
        with unittest.mock.patch('interface.cmdui.open', return_value=fake_banner, create=True):
            cli = self.create()
            cli.active_module = {'dir300_600_exec', 'dir890l_soapaction'}
            with unittest.mock.patch('sys.stdout', new=io.StringIO()) as mock_stdout:
                self.assertFalse(cli.onecmd("show"))
            self.assertEqual("""dir300_600_exec\ndir890l_soapaction""", mock_stdout.getvalue().strip())
        # These were just two basic edge tests for "show" more should be in place

    @unittest.mock.patch("interface.cmdui.loader")
    @unittest.mock.patch("interface.cmdui.interface.utils")
    def test_load_command_file(self, mock_loader, mock_utils):
        mock_loader.check_dependencies.return_value = None
        mock_loader.open_database.return_value = None

        fake_banner = io.StringIO("Yey banner.txt")
        with unittest.mock.patch('interface.cmdui.open', return_value=fake_banner, create=True):
            cli = self.create()
            cli.active_module = {'dir300_600_exec', 'dir890l_soapaction'}
            self.assertFalse(cli.onecmd("load dir300_600_exec"))
            self.assertTrue(mock_loader.load_module.called_with("modules.exploits.dlink.dir300_600_exec"))

    @unittest.mock.patch("interface.cmdui.loader")
    @unittest.mock.patch("interface.cmdui.interface.utils")
    def test_load_command_dir1(self, mock_loader, mock_utils):
        mock_loader.check_dependencies.return_value = None
        mock_loader.open_database.return_value = None

        fake_banner = io.StringIO("Yey banner.txt")
        with unittest.mock.patch('interface.cmdui.open', return_value=fake_banner, create=True):
            cli = self.create()
            cli.active_module = {'harvesters': {'airlive': {'WT2000ARM'}},
                                 'exploits': {'netgear': {'wndr_auth_bypass', 'n300_auth_bypass'},
                                              'zyxel': {'rom-0'},
                                              'zte': {'f660_config_download'},
                                              'linksys': {'ea6100_auth_bypass'},
                                              'dlink': {'dir890l_soapaction', 'dir300_600_exec'}}}
            self.assertFalse(cli.onecmd("load exploits"))
            self.assertEqual("exploits/", core.globals.active_module_path)
            core.globals.active_module_path = ""  # Clear active_module_path

    @unittest.mock.patch("interface.cmdui.loader")
    @unittest.mock.patch("interface.cmdui.interface.utils")
    def test_load_command_dir2(self, mock_loader, mock_utils):
        mock_loader.check_dependencies.return_value = None
        mock_loader.open_database.return_value = None

        fake_banner = io.StringIO("Yey banner.txt")
        with unittest.mock.patch('interface.cmdui.open', return_value=fake_banner, create=True):
            cli = self.create()
            cli.active_module = {'harvesters': {'airlive': {'WT2000ARM'}},
                                 'exploits': {'netgear': {'wndr_auth_bypass', 'n300_auth_bypass'},
                                              'zyxel': {'rom-0'},
                                              'zte': {'f660_config_download'},
                                              'linksys': {'ea6100_auth_bypass'},
                                              'dlink': {'dir890l_soapaction', 'dir300_600_exec'}}}
            self.assertFalse(cli.onecmd("load exploits/netgear"))
            self.assertEqual("exploits/netgear/", core.globals.active_module_path)
            core.globals.active_module_path = ""

    @unittest.mock.patch("interface.cmdui.loader")
    @unittest.mock.patch("interface.cmdui.interface.utils")
    def test_load_command_dir2(self, mock_loader, mock_utils):
        mock_loader.check_dependencies.return_value = None
        mock_loader.open_database.return_value = None

        fake_banner = io.StringIO("Yey banner.txt")
        with unittest.mock.patch('interface.cmdui.open', return_value=fake_banner, create=True):
            cli = self.create()
            cli.active_module = {'harvesters': {'airlive': {'WT2000ARM'}},
                                 'exploits': {'netgear': {'wndr_auth_bypass', 'n300_auth_bypass'},
                                              'zyxel': {'rom-0'},
                                              'zte': {'f660_config_download'},
                                              'linksys': {'ea6100_auth_bypass'},
                                              'dlink': {'dir890l_soapaction', 'dir300_600_exec'}}}
            self.assertFalse(cli.onecmd("load exploits/netgear"))
            self.assertEqual("exploits/netgear/", core.globals.active_module_path)
            self.assertFalse(cli.onecmd("unload"))
            self.assertEqual("", core.globals.active_module_path)
            self.assertEqual(cli.active_module, cli.modules)

    # TODO: This test is broken, hmm I don't know how to fix it right now
    # @unittest.mock.patch("interface.cmdui.loader")
    # @unittest.mock.patch("interface.cmdui.updater")
    # @unittest.mock.patch("interface.cmdui.interface.utils")
    # def test_update_command(self, mock_loader, mock_updater, mock_utils):
    #     mock_loader.check_dependencies.return_value = None
    #     mock_loader.open_database.return_value = None
    #     fake_banner = io.StringIO("Yey banner.txt")
    #     with unittest.mock.patch('interface.cmdui.open', return_value=fake_banner, create=True):
    #         cli = self.create()
    #
    #         with unittest.mock.patch('sys.stdout', new=io.StringIO()) as mock_stdout:
    #             self.assertFalse(cli.onecmd("update"))
    #             self.assertTrue(mock_updater.update_rext.assert_called())
    #             self.assertFalse(cli.onecmd("update force"))
    #             self.assertTrue(mock_updater.update_rext_force.assert_called())
    #             self.assertFalse(cli.onecmd("update oui"))
    #             self.assertTrue(mock_updater.update_oui.assert_called())

    # I don' believe it's possible to write unittest for autocomplete feature.

    # @unittest.mock.patch("interface.cmdui.loader")
    # @unittest.mock.patch("interface.cmdui.interface.utils")
    # def test_exit_command(self, mock_loader, mock_utils):
    #     mock_loader.check_dependencies.return_value = None
    #     mock_loader.open_database.return_value = None
    #     fake_banner = io.StringIO("Yey banner.txt")
    #     with unittest.mock.patch('interface.cmdui.open', return_value=fake_banner, create=True):
    #         cli = self.create()
    #
    #         with unittest.mock.patch('sys.stdout', new=io.StringIO()) as mock_stdout:
    #             self.assertTrue(cli.onecmd("exit"))
    #             self.assertTrue(mock_loader.close_database.assert_called_with())


if __name__ == '__main__':
    unittest.main()

