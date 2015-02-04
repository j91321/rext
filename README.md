Router Exploitation Toolkit - REXT
==================================

Small toolkit for easy creation and usage of various python scripts that work with embedded devices.


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


Requirements
============
I am trying to keep the requirements minimal:

- httplib2