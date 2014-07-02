#!/usb/bin/python3
import bisect

class BTree:
    MAX_CHILDREN = 33
    MAX_VALUES = MAX_CHILDREN - 1

g_root = None

class BTreeNode:
    def __init__(self, values=[], children=None):
        self.parent = None
        self.values = values
        self.children = children
        # make sure the children have the correct parent
        if self.children:
            for i in self.children:
                i.parent = self

    def __repr__(self):
        return 'BTreeNode(%s, %s, %r%s, %r%s)' % (
                hex(id(self)),
                hex(id(self.parent)) if self.parent else 'None',
                self.values[0:5],
                '' if len(self.values) <= 5 else ('\b... (%s values)' % len(self.values)),
                self.children[0:3] if self.children else None,
                '' if (not self.children or len(self.children) <= 3) else ('... %s values' % len(self.children)))

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
    return True if the add succeeded or False if the key
    already exists
    """
    def add(self, val, childNodes=None):
        if childNodes is None:
            found, node, slot = self.search(val)
            if found:
                # we don't allow duplicates
                return False
        else:
            assert(len(childNodes) == 2)
            node, slot = self, bisect.bisect_left(
                                        self.values, val)


        # all insertions should start at a leaf node,
        # unless we call add as a result of node spliting
        # when we are adding the median value to the parent
        assert(node.children is None or childNodes)

        if node.values_count() < BTree.MAX_VALUES:
            node.values.insert(slot, val)
            if node.children:
                # update the parent reference in the nodes we are about to add
                for i in childNodes:
                    i.parent = node
                node.children[slot:slot + 1] = childNodes
        else:
            # get the median of val and slots
            vl = node.values[:]
            vl.insert(slot, val)
            if len(vl) % 2 == 1:
                medianIdx = (len(vl) // 2)
            else:
                medianIdx = (len(vl) // 2) - 1
            median = vl[medianIdx]
            cl = None
            if node.children:
                cl = node.children[:]
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

            if node.parent:  # TODO: is the parent preserved ???
                node.parent.add(median, (leftNode, rightNode))
            else:
                # create new root and increment the tree depth
                newParent = BTreeNode([ median ], [leftNode, rightNode])
                leftNode.parent = newParent
                rightNode.parent = newParent

                global g_root
                g_root = newParent

        return True


def btree_test():
    global g_root
    g_root = BTreeNode()
    # for i in range(15, 0, -1):
    # for i in [5, 3, 21, 9, 1, 13, 2, 7, 10, 12, 4, 8]:
    for i in range(0, 10000):
        print("insert: %s" % i)
        g_root.add(i)
        print('%r' % (g_root))
    print("-------")
    g_root.search(77799)
    for i in range(0, 10000):
        if not g_root.search(i)[0]:
            raise
    print("Done.")
        
#     root = root.add(6)
#     root = root.add(2)
#     root = root.add(4)
#     root = root.add(8)
#     root = root.add(0)
#     root = root.add(5)
    # print('%r' % (g_root))

btree_test()

