Router Exploitation Toolkit - REXT
==================================

Small toolkit for easy creation and usage of various python scripts that work with embedded devices.

[![Build Status](https://travis-ci.org/j91321/rext.svg?branch=master)](https://travis-ci.org/j91321/rext)

- core - contains most of toolkits basic functions
- databases - contains databases, like default credentials etc.
- interface - contains code that is being used for the creation and manipulation with interface
- modules - contains structure of modules, that can be loaded, every module contains vendor specific sub-modules where scripts are stored.
    - decryptors
    - exploits
    - harvesters
    - misc
    - scanners
- output - output goes here

This is still heavy work-in progress

TODO
====


- Porting javascript exploits from routerpwn.com (not always in the most pythonic way) - feel free to contribute
- More and better tests
- More modules

Requirements
============
I am trying to keep the requirements minimal:

- requests
- paramiko
- beautifulsoup4

License
=======
This software is licensed under GNU GPL v3. For more information please see LICENSE file