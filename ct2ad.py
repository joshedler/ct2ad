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

    print(f'loaded {len(rows)} total nodes...')

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

    print(f'loaded {len(rows)} total children...')

    return rows

def sql_get_child_by_node_id(con, node_id):
    '''
    Get the node with matching node_id from the CherryTree database.

    :param con: sqlite3 connection object
    :param node_id: the node_id to return
    :return: returns a list of tuple rows from the database (node_id, name, txt)
    '''
    c = con.cursor()

    a = (node_id,)
    c.execute('SELECT node_id, father_id, sequence FROM children WHERE node_id = ?', a)

    # 'rows' are of type list
    # each 'row' is of type tuple
    rows = c.fetchall()

    return rows

def expand_child(child, all_nodes):
    '''
    Given a child tuple, return the matching node_id as a dictionary.

    :param child: a child tuple(node_id, father_id, sequence)
    :param all_nodes: the dictionary of all nodes from the database
    :return: returns a node as a dictionary object with keys
             'node' as tuple (node_id, name, txt),
             'father' as tuple (node_id, name, txt), and
             'seq' as integer
    '''
    node = all_nodes[child[0]]
    father = all_nodes[child[1]] if child[1] > 0 else None
    seq = child[2]

    return {'node': node, 'father': father, 'seq': seq}

def get_father_for_node(node, all_children, all_nodes):
    '''
    Find the father for a given node.

    :param node: the starting node for which the father is desired
    :param all_children: the list of all children from the database
    :param all_nodes: the dictionary of all nodes from the database
    :return: returns the father node (node_id, name, txt) if there is one or None
    '''
    node_id = get_node_id(node)

    for c in all_children:
        if c[0] == node_id:
            xc = expand_child(c, all_nodes)
            return get_expanded_child_father(xc)

    return None

def get_expanded_child_node(xc):
    return xc['node']

def get_expanded_child_father(xc):
    return xc['father']

def get_expanded_child_seq(xc):
    return xc['seq']

def get_node_txt(node):
    '''
    Returns the txt field from a node tuple (node_id, name, txt)

    :param node: a node tuple (node_id, name, txt)
    :return: returns the string representing the txt field
    '''
    return node[2]

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

def dig(father, all_children, all_nodes, level):
    '''
    Given a father, recursively dig through the children, yielding(expanded_child_node, level) along the way.

    :param father: a father as an "expanded child" dictionary node with keys 'node', 'father', and 'seq'
    :param all_children: the list of all children from the database
    :param all_nodes: the dictionary of all nodes from the database
    :level: an integer, beginning with 1, representing the indent level for nice output
    :return: returns nothing
    '''
    father_id = father['node'][0]

    children = list(filter(lambda c: c[1] == father_id, all_children))

    xc_list = []
    for child in children:
        xc = expand_child(child, all_nodes)
        xc_list.append(xc)

    for xc in sorted(xc_list, key=sequence_order):
        yield(xc, level)

        for xc_n, l in dig(xc, all_children, all_nodes, level+1):
            yield(xc_n, l)

def sequence_order(expanded_child):
    '''
    A function allowing sorted() to iterate over a list of expanded_child dictionary objects in the proper sequence.
    '''
    return expanded_child['seq']
