#! /usr/bin/env python3

import argparse
import colorama
from colorama import Fore, Back, Style
import pathlib
import re
import sqlite3
import sys

from ct2ad import *

def get_safe_file_name(node):
    '''
    Gets a "safe" file name from the node name, replacing characters that are not filesystem-friendly
    with safer alternatives.
    '''
    name = get_node_name(node)
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'/', '+', name)
    return name

def export(xc_nodes, args, all_children, all_nodes):
    '''
    Export a list of "expanded child" nodes.

    :param xc_nodes: the list of "expanded child" nodes to export
    :args: command-line arguments for output file handling
    :param all_children: the list of all children from the database
    :param all_nodes: the dictionary of all nodes from the database
    :return: returns nothing
    '''
    real_stdout = sys.stdout

    root_path = pathlib.Path('.')

    if args.output_folder is not None:
        root_path = pathlib.Path(args.output_folder)

    for xc_node in xc_nodes:
        node = get_expanded_child_node(xc_node)
        father = get_expanded_child_father(xc_node)
        node_path = pathlib.Path()

        # build up the node_path with father information
        while father is not None:
            node_path = get_safe_file_name(father) / node_path
            father = get_father_for_node(father, all_children, all_nodes)

        node_path = root_path / node_path

        print(f'Exporting {Fore.YELLOW+Style.BRIGHT}{get_node_name(node)}{Style.RESET_ALL}...' ,end='')

        f = None

        if args.output_to_stdio is False:
            if args.output_name is not None:
                print(f'  {Style.DIM}{args.output_name}')
                f = open(args.output_name, 'w')
                sys.stdout = f
            else: # args.output_folder must be True
                file_name = node_path / f'{get_safe_file_name(node)}.xml'
                print(f'  {Style.DIM}{file_name}')
                node_path.mkdir(parents=True, exist_ok=True)
                f = file_name.open('w')
                sys.stdout = f

        print(get_node_txt(node))

        if f is not None:
            sys.stdout = real_stdout
            f.close()
            f = None


# setup argument parsing...
parser = argparse.ArgumentParser(description=__doc__)

parser.add_argument('sqlite3_db', action='store')

node_options = parser.add_mutually_exclusive_group(required=True)
node_options.add_argument('-a', action='store_true', dest='export_all', help='Export all nodes')
node_options.add_argument('-b', action='store', dest='branch_id', help='Export a branch starting at node_id')
node_options.add_argument('-n', action='store', dest='node_id', help='Export a single node by node_id')

output_options = parser.add_mutually_exclusive_group(required=True)
output_options.add_argument('-o', action='store', dest='output_name', help='Output file name to export to (will overwrite existing without warning)')
output_options.add_argument('-O', action='store', dest='output_folder', help='Output folder to export for branch/all options (note: file name uses node name)')
output_options.add_argument('-1', action='store_true', dest='output_to_stdio', help='Output to stdio')

args = parser.parse_args()

colorama.init(autoreset=True)

# load the database and party on!
con = sqlite3.connect(args.sqlite3_db)

results = [ ]

# treat a branch like a single node with a dig
if args.branch_id is not None:
    args.node_id = args.branch_id
    args.export_branch = True
else:
    args.export_branch = False

if args.output_name is not None:
    if args.export_all or args.export_branch:
        print(f'{Fore.RED+Style.BRIGHT}ERROR: single output file with multiple node exports is not supported')
        sys.exit(1)

# all_nodes are a dict with each key being the unique node_id
all_nodes = sql_get_all_nodes(con)

# all_children are a list of tuples
all_children = sql_get_all_children(con)

if args.node_id is not None:
    if not re.match(r'^\d+$', args.node_id):
        print(f'{Fore.RED+Style.BRIGHT}ERROR: node_id argument is not a number')
        sys.exit(1)

    if not args.export_branch:
        print(f'Searching for node with node_id matching {args.node_id}...')
        children = sql_get_child_by_node_id(con, args.node_id)

        for child in children:
            results.append(expand_child(child, all_nodes))
    else:
        node_id = int(args.node_id)
        xc_father = expand_child(next(c for c in all_children if c[0] == node_id), all_nodes)
        results.append(xc_father)

        for xc_node, level in dig(xc_father, all_children, all_nodes, 1):
            results.append(xc_node)
else: #args.export_all
    xc_roots = []

    for child in all_children:
        xc = expand_child(child, all_nodes)

        if get_expanded_child_father(xc) == None: xc_roots.append(xc)

    for xc in sorted(xc_roots, key=sequence_order):
        results.append(xc)

        for xc_node, level in dig(xc, all_children, all_nodes, 1):
            results.append(xc_node)


    print(f'{len(results)} matching nodes found.')

if len(results) > 0:
    export(results, args, all_children, all_nodes)
