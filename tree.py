#! /usr/bin/env python3

'''
Examine a CherryTree SQLite database and print out the tree in proper heirarchical form and sequence.
'''

import argparse
import colorama
from colorama import Fore, Back, Style
import sqlite3

from ct2ad import *

def print_xc_node(xc_node, level):
    '''
    Print the node information to the console in a nice format
    '''
    indent = '--' * level
    s = get_expanded_child_seq(xc_node)
    n = get_expanded_child_node(xc_node)
    print(f'{Style.DIM}|{indent} {Style.NORMAL}{s:03}: {Style.BRIGHT+Fore.YELLOW}\'{get_node_name(n)}\' {Fore.RESET}{Style.DIM}: [node_id = {get_node_id(n)}]')

# setup argument parsing...
parser = argparse.ArgumentParser(description=__doc__)

parser.add_argument('sqlite3_db', action='store')

args = parser.parse_args()

colorama.init(autoreset=True)

# load the database and party on!
con = sqlite3.connect(args.sqlite3_db)

sql_get_tables(con)

# all_nodes are a dict with each key being the unique node_id
all_nodes = sql_get_all_nodes(con)

# all_children are a list of tuples
all_children = sql_get_all_children(con)

xc_roots = []

for child in all_children:
    xc_root = expand_child(child, all_nodes)

    if get_expanded_child_father(xc_root) == None: xc_roots.append(xc_root)

print()

count = 0

for xc_root in sorted(xc_roots, key=sequence_order):
    count = count + 1
    print_xc_node(xc_root, 0)

    for xc, level in dig(xc_root, all_children, all_nodes, 1):
        print_xc_node(xc, level)
        count = count + 1

print(f'\n{count} nodes iterated over')
