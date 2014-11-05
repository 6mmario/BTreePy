#!/usr/bin/python3

# BTree - B-tree implementation in Python for didactic purposes.
#
# It includes algorithms to add, search and delete values from 
# the B-tree. It was inspired by this Wikipedia article:
#         https://en.wikipedia.org/wiki/Btree
# Searching within nodes is done using binary search (using 
# the bisect module).
#
# @copyright: Copyright (c) 2014 Robert Zavalczki, distributed
# under the terms and conditions of the Lesser GNU General 
# Public License version 2.1

import bisect

""" A B-tree node is a concrete class. It holds an ordered list 
    of values and - in case of inner nodes - the list of the 
    corresponding BTreeNode children which are separated by 
    those values. The parent member references the parent node
    or None in the case of the root node.
"""
class BTreeNode(object):
    def __init__(self, values=None, children=None):
        self.parent = None
        if values is None:
            self.values = []
        else:
            self.values = values
        self.children = children
        # update the parent node in children, 
        # just in case it has changed
        if self.children:
            for i in self.children:
                i.parent = self

    def __str__(self):
        return 'Node(%x, %x, %r, %d)' % (
                id(self),
                id(self.parent),
                self.values,
                len(self.children) if self.children else 0)
        
    def pretty_print(self, tab=''):
        print('%s%s' % (tab, self))
        if self.children:
            for i in self.children:
                i.pretty_print(tab + '   ')

    """ Check (recursively) tree integrity according to the B-tree rules. 
        This is used to check the correctness of algorithms.
    """
    def check_valid(self, tree):
        innerNode = self.children is not None
        rootNode = self.parent is None

        assert(self.values is not None)

        # an inner node except the root has at least min_values
        if not rootNode and innerNode:
            assert(tree.min_values <= len(self.values))

        # a node can't have more than max_values
        assert(len(self.values) <= tree.max_values)

        # The root has at least two children if it is not a leaf node.
        if rootNode and innerNode:
            assert(len(self.children) >= 2)

        # A non-leaf node with k children contains k-1 keys.
        if innerNode:
            assert((len(self.values) + 1) == len(self.children))
        
        # check that values are sorted
        prev = None
        for i in self.values:
            if prev is not None:
                assert(i > prev)
            prev = i

        if self.children:
            for i in self.children:
                assert(i.parent is self)
                i.check_valid(tree)


    """
    Search for a value starting with this node.
    
    If the value does not exist in the tree, move down the tree and 
    return the leaf node and the insertion position in that node where
    the value should be placed. i.e the tupple: (False, node, pos)

    If val exists in the tree return the tupple: (True, node, pos),
    where node is the node containing the value and pos is the 
    position of the value within that node.
    """
    def search(self, val):
        i = bisect.bisect_left(self.values, val)
        if (i != len(self.values) and not val < self.values[i]):
            # a value was found
            assert(self.values[i] == val)
            return (True, self, i)            

        if self.children is not None:
            assert(len(self.children) >= i and self.children[i])
            # recursively search down the appropriate child node
            return self.children[i].search(val)
        else:
            return (False, self, i)

    """ Split a B-tree node in two.
    
        If val and slot are given then also insert val into the
        resulting nodes. If additionally childNodes is given 
        then _split_node is recursively called from add and
        childNodes represent the nodes separated by the value val
        in this node's parent.
    """    
    def _split_node(self, tree, val=None, slot=None, childNodes=None):
        assert(val is None or (slot is not None))

        midList = [] if val is None else [ val ]
        if slot is None:
            slot = 0

        # get the median of self.values and val
        splitValues = self.values[0:slot] + midList + self.values[slot:]
        medianIdx = len(splitValues) // 2
        
        lv = splitValues[0:medianIdx]
        medianVal = splitValues[medianIdx]
        rv = splitValues[medianIdx + 1:]
        
        innerNode = self.children is not None

        if innerNode:
            if childNodes is not None:
                splitChildren = (self.children[0:slot] + 
                                 list(childNodes) + 
                                 self.children[slot + 1:])
            else:
                splitChildren = self.children
            lc = splitChildren[0:len(lv) + 1]
            rc = splitChildren[len(lv) + 1:]
        else:
            lc = None
            rc = None

        leftNode = BTreeNode(lv, lc)
        rightNode = BTreeNode(rv, rc)

        if self.parent:
            self.parent.add(tree,
                            medianVal,
                            None,
                            (leftNode, rightNode))
        else:
            # create new root and increment the tree depth
            newRoot = BTreeNode([ medianVal ], [leftNode, rightNode])
            leftNode.parent = newRoot
            rightNode.parent = newRoot
            tree.root = newRoot
            tree.height += 1
            tree.size += 1
        

    """
    Add a new value to the B-tree 'tree'.
    
    The value must not already exist.
    """
    def add(self, tree, val, slot=None, childNodes=None):
        # all insertions should start at a leaf node,
        # unless we call add recursively into the parent
        # as a result of node splitting
        # when we are adding the median value to the parent
        assert(self.children is None or childNodes)

        # if this is an inner node if not a leaf or the root
        # then self.children is not None, then also
        # this function must have been called recursively
        # with childNodes not None, val not None and 
        # len(childNodes) == 2
        innerNode = self.children is not None
        if innerNode:
            assert(childNodes and len(childNodes) == 2)
        else:
            assert(childNodes is None)
        
        # if not already found, find the insert position among 
        # the current node's values
        if slot is None:
            slot = bisect.bisect_left(self.values, val)

        # can we do the insertion to the current node values?
        if len(self.values) < tree.max_values:
            self.values.insert(slot, val)
            tree.size += 1
            if childNodes:
                # update the parent reference in the nodes we are about to add
                for i in childNodes:
                    i.parent = self
                self.children[slot:slot + 1] = childNodes
            # we're done
            return True
        
        # it seems the current node is full, we have to split it
        self._split_node(tree, val, slot, childNodes)
        return True


    def min_value(self, slot=0):
        if self.children:
            return self.children[slot].min_value()
        return self.values[0], self, 0

    def max_value(self, slot=None):
        if slot is None:
            slot = len(self.values) - 1
        if self.children:
            return self.children[slot + 1].max_value()
        return self.values[-1], self, len(self.values) - 1


    """
    Delete a value from the B-tree.
    The value must exist.
    """
    def delete(self, tree, val, slot=None):

        innerNode = self.children is not None        
        if slot is None:
            assert(slot is not None)
            slot = bisect.bisect_left(self.values, val)
        
        assert(slot != len(self.values) and self.values[slot] == val)
        
        if not innerNode:
            # perform deletion from a leaf
            del self.values[slot]
            tree.size -= 1
            if len(self.values) < tree.min_values:
                # underflow happened in the leaf node
                # rebalance tree starting with this node
                self._rebalance(tree)
        else:
            # find the minimum value in the right subtree
            # and use it as the separator value to replace val
            newSep, node, idx = self.min_value(slot + 1)
            self.values[slot] = newSep
            del node.values[idx]
            tree.size -= 1
            if len(node.values) < tree.min_values:
                node._rebalance(tree)

    """ Rebalance a B-tree starting with the current node.
    """
    def _rebalance(self, tree):
        lsibling, rsibling, idx = self.get_siblings()
        
        # only the root doesn't have siblings
        assert(rsibling or lsibling or self.parent is None)

        if self.parent is None:
            # this is a no-op for the root node
            return

        innerNode = self.children is not None
        if innerNode:
            assert(rsibling is None or rsibling.children is not None)
            assert(lsibling is None or lsibling.children is not None)
        else:
            assert(rsibling is None or rsibling.children is None)
            assert(lsibling is None or lsibling.children is None)

        if not innerNode:
            if rsibling and len(rsibling.values) > tree.min_values:
                sepIdx = idx
                sepVal = self.parent.values[sepIdx]
                # borrow node from rsibling to perform a left rotate
                self.parent.values[sepIdx] = rsibling.values[0]
                del rsibling.values[0]
                self.values.append(sepVal)
                return
            elif lsibling and len(lsibling.values) > tree.min_values:
                sepIdx = idx - 1
                sepVal = self.parent.values[sepIdx]
                # borrow node from lsibling to perform a right rotate
                self.parent.values[sepIdx] = lsibling.values[-1]
                del lsibling.values[-1]
                self.values.insert(0, sepVal)
                return

        # we have to merge 2 nodes
        if lsibling is not None:
            sepIdx = idx - 1
            ln = lsibling
            rn = self
        elif rsibling is not None:
            sepIdx = idx
            ln = self
            rn = rsibling
        else:
            assert(False)
        
        sepVal = self.parent.values[sepIdx]

        ln.values.append(sepVal)
        ln.values.extend(rn.values)
        del rn.values[:]
        del self.parent.values[sepIdx]
        assert(self.parent.children[sepIdx + 1] is rn)
        del self.parent.children[sepIdx + 1]
        if rn.children:
            ln.children.extend(rn.children)
            for i in rn.children:
                i.parent = ln

        if len(ln.values) > tree.max_values:
            # we have to split the newly formed node
            # this situation can aris only when merging inner nodes
            assert(innerNode)
            ln._split_node(tree)

        if len(self.parent.values) < tree.min_values:
            # rebalance the parent
            self.parent._rebalance(tree)            

        if self.parent.parent is None and not self.parent.values:
            tree.root = ln
            tree.root.parent = None

    """ Get the adjacent siblings of this node.
     
    Return the tupple:
    (left sibiling node, right sibling node, separator index).
    If a sibling does not exist, None is returned instead. The 
    separator index represents the index of this node in its 
    parent's children list.
    """
    def get_siblings(self):
        if not self.parent:
            # the root doesn't have siblings
            return (None, None, 0)

        assert(self.parent.children)

        lsibling = None
        rsibling = None
        idx = 0

        for i, j in enumerate(self.parent.children):
            if j is self:
                if i != 0:
                    lsibling = self.parent.children[i - 1]
                if (i + 1) < len(self.parent.children):
                    rsibling = self.parent.children[i + 1]
                idx = i  
                break

        return (lsibling, rsibling, idx)

""" B-tree implementation operating on BTreeNode-s.
    
    It implements the interface for constructing, editing and 
    searching in B-trees.
"""
class BTree(object):
    
    def __init__(self, max_values):
        if max_values <= 1:
            raise ValueError("B-tree max_values count per node must be at least 2")
        self.root = BTreeNode()
        self.max_values = max_values
        self.min_values = max_values // 2
        self.height = 1
        self.size = 0
        
    def __str__(self):
        return 'height: %d items: %d m: %d root: %x' % (
                                    self.height, self.size,
                                    self.max_values + 1,
                                    id(self.root))

    def add(self, val):
        # find the leaf node where the value should be added
        found, node, slot = self.root.search(val)
        if found:
            # the value already exists, can't add it twice
            return False
        return node.add(self, val, slot, None)

    def delete(self, val):
        # find the value and its
        found, node, slot = self.root.search(val)
        if not found:
            # the value doesn't exist, can't delete it
            return False
        return node.delete(self, val, slot)

    def search(self, val):
        return self.root.search(val)[0]

    def min(self):
        return self.root.min_value()[0]

    def max(self):
        return self.root.max_value()[0]
    


def check_tree(tree, values):
    for i in values:
        assert(tree.search(i))

    if values:
        assert(not tree.search(min(values) - 1))
        assert(not tree.search(max(values) + 1))

    if tree.size and values:
        assert(tree.min() == min(values))
        assert(tree.max() == max(values))

def btree_test():
    tree = BTree(3)
    values = [i for i in range(1, 36, 2)]
    values.extend([i for i in range(100, 200, 13)])
    values.extend([i for i in range(10, 20, 2)])
    values.extend([i for i in range(119, 200, 17)])
    print(values)

    for i in values:
        print('adding: %s ...' % (i))
        tree.add(i)
        tree.root.pretty_print()
        print("-------")  
        tree.root.check_valid(tree)
    
    print(tree)
    tree.root.pretty_print()     
    print("-------")

    for i in values[:]:
        print('removing: %s ...' % (i))
        tree.delete(i)
        tree.root.pretty_print()
        print("-------")
        tree.root.check_valid(tree)
        values.remove(i)
        check_tree(tree, values)

    print("Done.")


# btree_test()

import random

def rand_test(max_values=3, count=11, seed=None):
    if seed is None:
        random.seed(17)
    else:
        random.seed(int(seed))

    n = max_values  # random.randint(4, 16)
    tree = BTree(n)
    n = count  # random.randint(1, 360)
    print("test values: %d" % (count))
    
    values = [random.randint(1000, 9999) for i in range(0, n)]
    # values = [4444, 3625, 1391, 9257, 5453, 9803, 4565, 3270, 7259, 2904, 3447, 7400, 5966, 5882]
    print(values)

    for i in values[:]:
        # print('adding: %s ...' % (i))
        if not tree.add(i):
            # print('duplicate: %s ...' % (i))
            values.remove(i)
        # print(tree)
        # tree.root.pretty_print()
        # print("-------")  
        tree.root.check_valid(tree)
    
    print(tree)
    tree.root.pretty_print()     
    print("-------")

    random.shuffle(values)
    for i in values[:]:
        # print('removing: %s ...' % (i))
        tree.delete(i)
        # tree.root.pretty_print()
        # print("-------")
        tree.root.check_valid(tree)
        values.remove(i)
        check_tree(tree, values)

    print("Done.")


# rand_test(3, 19, 120804)

if 1:
    mini = 99999
    for seed in range(120859, 120869):
        for i in range(99, 150):
            try:
                rand_test(19, i, seed)
            except:
                print("i: %d min: %d seed: %d" % (i, mini, seed))
                if i < mini:
                    mini = i
                    raise
                raise
                break
