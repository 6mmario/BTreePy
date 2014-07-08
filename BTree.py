#!/usr/bin/python3
import bisect


class BTreeNode:
    def __init__(self, values=None, children=None):
        self.parent = None
        if values is None:
            self.values = []
        else:
            self.values = values
        self.children = children
        # make sure the children have the correct parent
        if self.children:
            for i in self.children:
                i.parent = self

    def __repr__(self):
        return 'BTreeNode(%x, %x, %r, %r)' % (
                id(self),
                id(self.parent),
                self.values,
                self.children)

    """
    Get the number of values in this node. This is the same
    as the number of children - 1 for non-leaf nodes.
    """
    def values_count(self):
        return len(self.values)

    """
    If val does not exist in the tree, search down and return 
    the leaf node and the insertion position in that node where
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
            return self.children[i].search(val)
        else:
            return (False, self, i)

    """
    return the new root if it changed, otherwise return none
    """
    def _add(self, tree, val, slot=None, childNodes=None):
        # all insertions should start at a leaf node,
        # unless we call add as a result of node spliting
        # when we are adding the median value to the parent
        assert(self.children is None or childNodes)
        
        if slot is None:
            slot = bisect.bisect_left(self.values, val)

        if self.values_count() < tree.max_values:
            self.values.insert(slot, val)
            tree.size += 1
            if childNodes:
                # update the parent reference in the nodes we are about to add
                for i in childNodes:
                    i.parent = self
                self.children[slot:slot + 1] = childNodes
        else:
            # get the median of val and slots
            vl = self.values[:]
            vl.insert(slot, val)
            if len(vl) % 2 == 1:
                medianIdx = (len(vl) // 2)
            else:
                medianIdx = (len(vl) // 2) - 1
            median = vl[medianIdx]
            cl = None
            if childNodes:
                cl = self.children[:]
                cl[slot:slot + 1] = childNodes

            # construct new left node
            vl1 = vl[0:medianIdx]
            cl1 = None
            if cl:
                cl1 = cl[0:medianIdx + 1]
            leftNode = BTreeNode(vl1, cl1)
            # construct the right node
            vl2 = vl[medianIdx + 1:]
            cl2 = None
            if cl:
                cl2 = cl[medianIdx + 1:]
            rightNode = BTreeNode(vl2, cl2)

            if self.parent:
                self.parent._add(tree, median, None, (leftNode, rightNode))
            else:
                # create new root and increment the tree depth
                newParent = BTreeNode([ median ], [leftNode, rightNode])
                leftNode.parent = newParent
                rightNode.parent = newParent
                tree.root = newParent
                tree.height += 1
                tree.size += 1


class BTree:
    
    def __init__(self, max_values=2):
        self.root = BTreeNode()
        self.max_values = max_values
        self.height = 1
        self.size = 0
        
    def __repr__(self):
        return '%d %d %d %x' % (self.height, self.size,
                                self.max_values,
                                id(self.root))

    def search(self, val):
        return self.root.search(val)[0]

    def add(self, val):
        # find the leaf node where the value should be added
        found, node, slot = self.root.search(val)
        if found:
            # the value already exists, can't add it twice
            return False
        node._add(self, val, slot, None)


def btree_test():
    tree = BTree(4)
    # for i in range(15, 0, -1):
    # for i in [5, 3, 21, 9, 1, 13, 2, 7, 10, 12, 4, 8]:
    for i in range(1, 16):
        print("insert: %s" % i)
        tree.add(i)
        print('%r\n%r' % (tree, tree.root))
    print("-------")
    tree.search(77799)
    for i in range(1, 16):
        if not tree.search(i):
            raise
    print("Done.")

btree_test()

