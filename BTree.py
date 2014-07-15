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

    def check_valid(self):
        assert(self.values is not None)
        prev = None
        for i in self.values:
            if prev is not None:
                assert(i > prev)
            prev = i
            
        assert(self.children is None or 
               (len(self.values) + 1) == len(self.children))

        if self.children:
            for i in self.children:
                assert(i.parent is self)
                i.check_valid()                



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
    add a new value to the B-Tree, the value must not already exist
    """
    def _add(self, tree, val, slot=None, childNodes=None):
        # all insertions should start at a leaf node,
        # unless we call _add recursively into the parent
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
        
        if slot is None:
            slot = bisect.bisect_left(self.values, val)

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
       
        # get the median of self.values and val
        medianIdx = len(self.values) // 2

        # lists of new child nodes split by the median value that 
        # we are to determine
        if innerNode:
            lc = []
            rc = []
        else:
            lc = None
            rc = None
        
        if slot < medianIdx:
            lv = self.values[0:slot]
            lv.extend([ val ])
            lv.extend(self.values[slot:medianIdx])
            medianVal = self.values[medianIdx]
            rv = self.values[medianIdx + 1:]
            if innerNode:
                lc = self.children[0:slot]
                lc.extend(childNodes)
                lc.extend(self.children[slot + 1:medianIdx + 1])
                rc.extend(self.children[medianIdx + 1:])
        elif slot == medianIdx:
            lv = self.values[0:medianIdx]
            medianVal = val
            rv = self.values[medianIdx:]
            if innerNode:
                lc.extend(self.children[0:medianIdx])
                lc.extend([ childNodes[0] ])
                rc.extend([ childNodes[1] ])
                rc.extend(self.children[medianIdx + 1:])
        else:
            # slot > medianIdx
            lv = self.values[0:medianIdx]
            medianVal = self.values[medianIdx]
            rv = self.values[medianIdx + 1:slot]
            rv.extend([ val ])
            rv.extend(self.values[slot:])
            if innerNode:
                lc.extend(self.children[0:medianIdx + 1])
                rc.extend(self.children[medianIdx + 1:slot])
                rc.extend(childNodes)
                rc.extend(self.children[slot + 1:])

        leftNode = BTreeNode(lv, lc)
        rightNode = BTreeNode(rv, rc)

        if self.parent:
            return self.parent._add(tree,
                                    medianVal,
                                    None,
                                    (leftNode, rightNode))

        # create new root and increment the tree depth
        newRoot = BTreeNode([ medianVal ], [leftNode, rightNode])
        leftNode.parent = newRoot
        rightNode.parent = newRoot
        tree.root = newRoot
        tree.height += 1
        tree.size += 1
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
    delete a value from the B-Tree, the value must exist
    """
    def _delete(self, tree, val, slot=None):

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

    def _rebalance(self, tree):
        lsibling, rsibling, idx = self.get_siblings()
        
        # only the root doesn't have siblings
        # print('rebalance: %s <- %s -> %s' % (lsibling, self, rsibling))
        assert(rsibling or lsibling or self.parent is None)

        if self.parent is None:
            return False  # ???

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
                return True
            elif lsibling and len(lsibling.values) > tree.min_values:
                sepIdx = idx - 1
                sepVal = self.parent.values[sepIdx]
                # borrow node from lsibling to perform a right rotate
                self.parent.values[sepIdx] = lsibling.values[-1]
                del lsibling.values[-1]
                self.values.insert(0, sepVal)
                return True
        
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

        if self.parent.parent is None and not self.parent.values:
            tree.root = ln
            tree.root.parent = None
            return True
        
        if len(self.parent.values) < tree.min_values:
            # rebalance the parent
            self.parent._rebalance(tree)
            # raise Exception('Implement me!!!')
         

    
    """
    return the tupple: 
    (left sibiling node, right sibling node, separator index)
    If a sibling does not exist, None is returned
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


class BTree:
    
    def __init__(self, max_values=2):
        self.root = BTreeNode()
        self.max_values = max_values
        self.min_values = max_values // 2
        self.height = 1
        self.size = 0
        
    def __repr__(self):
        return '%d %d %d %x' % (self.height, self.size,
                                self.max_values,
                                id(self.root))

    def add(self, val):
        # find the leaf node where the value should be added
        found, node, slot = self.root.search(val)
        if found:
            # the value already exists, can't add it twice
            return False
        return node._add(self, val, slot, None)

    def delete(self, val):
        # find the value and its
        found, node, slot = self.root.search(val)
        if not found:
            # the value doesn't exist, can't delete it
            return False

        return node._delete(self, val, slot)


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
    tree = BTree(4)

    values = [i for i in range(1, 36, 2)]
    values.extend([i for i in range(10, 20, 2)])
    print(values)

    for i in values:
        tree.add(i)
        tree.root.check_valid()
    
    tree.root.pretty_print()     
    print("-------")

    for i in values[:]:
        tree.delete(i)
        tree.root.check_valid()
        tree.root.pretty_print()
        print("-------")
        values.remove(i)
        check_tree(tree, values)

    print("Done.")


btree_test()


