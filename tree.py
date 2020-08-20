#! /usr/bin/env python3

'''
Examine a CherryTree SQLite database and print out the tree in proper heirarchical form and sequence.
'''

import argparse
import colorama
from colorama import Fore, Back, Style
import sqlite3

def sql_get_tables(con):
    '''
    Print the tables found in the SQLite database.

    :param con: sqlite3 connection object
    :return: returns nothing
    '''
    c = con.cursor()

    c.execute('SELECT name from sqlite_master where type= "table"')

    print('found tables:')
    print(f'  {c.fetchall()}')

def sql_get_all_nodes(con):
    '''
    Get all nodes from the CherryTree database.

    :param con: sqlite3 connection object
    :return: returns a dictionary, with keys being node_id and values being
             the original tuple row from the database (node_id, name, txt)
    '''
    c = con.cursor()

    c.execute('SELECT node_id, name, txt from node')

    # 'rows' are of type list
    # each 'row' is of type tuple
    rows = c.fetchall()

    print(f'found {len(rows)} nodes...')

    results = { }

    for row in rows:
        results[row[0]] = row

    return results

def sql_get_all_children(con):
    '''
    Get all children from the CherryTree database.

    :param con: sqlite3 connection object
    :return: returns the children as a list of tuple(node_id, father_id, sequence)
    '''
    c = con.cursor()

    c.execute('SELECT node_id, father_id, sequence from children')

    # 'rows' are of type list
    # each 'row' is of type tuple
    rows = c.fetchall()

    print(f'found {len(rows)} children...')

    return rows

def get_node_from_child(child, all_nodes):
    '''
    Given a child tuple, return the matching node_id as a dictionary.

    :param child: a child tuple(node_id, father_id, sequence)
    :param all_nodes: a dictionary of nodes
    :return: returns a node as a dictionary object with keys
             'node' as tuple (node_id, name, txt),
             'father' as tuple (node_id, name, txt), and
             'seq' as integer
    '''
    node = all_nodes[child[0]]
    father = all_nodes[child[1]] if child[1] > 0 else None
    seq = child[2]

    return {'node': node, 'father': father, 'seq': seq}

def get_node_name(node):
    '''
    Returns the name field from a node tuple (node_id, name, txt)

    :param node: a node tuple (node_id, name, txt)
    :return: returns the string representing the name field
    '''
    return node[1]

def get_node_id(node):
    '''
    Returns the node_id field from a node tuple (node_id, name, txt)

    :param node: a node tuple (node_id, name, txt)
    :return: returns the node_id field
    '''
    return node[0]

def print_node(node, level):
    '''
    Print the node information to the console in a nice format
    '''
    indent = '--' * level
    s = node['seq']
    n = node['node']
    print(f'{Style.DIM}|{indent} {Style.NORMAL}{s:03}: {Style.BRIGHT+Fore.YELLOW}\'{get_node_name(n)}\' {Fore.RESET}{Style.DIM}: [node_id = {get_node_id(n)}]')

def dig(father, all_children, all_nodes, level):
    '''
    Given a father, recursively dig through the children, printing out
    node information along the way.

    :param father: a father as a dictionary node with keys 'node', 'father', and 'seq'
    :param all_children: the list of all children from the database
    :param all_nodes: the dictionary of all nodes from the database
    :level: an integer, beginning with 1, representing the indent level for nice output
    :return: returns a count of nodes discovered
    '''
    father_id = father['node'][0]

    children = list(filter(lambda c: c[1] == father_id, all_children))

    nodes = []
    for child in children:
        node = get_node_from_child(child, all_nodes)

        nodes.append(node)

    count = 0
    for node in sorted(nodes, key=sequence_order):
        count = count + 1
        print_node(node, level)

        count = count + dig(node, all_children, all_nodes, level+1)

    return count

def sequence_order(node):
    '''
    A function allowing sorted() to iterate over nodes in the proper sequence.
    '''
    return node['seq']

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

roots = []

for child in all_children:
    n = get_node_from_child(child, all_nodes)

    if n['father'] == None: roots.append(n)

print()

count = 0

for root in sorted(roots, key=sequence_order):
    count = count + 1
    print_node(root, 0)

    count = count + dig(root, all_children, all_nodes, 1)

print(f'\n{count} nodes iterated over')
