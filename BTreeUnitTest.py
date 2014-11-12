#!/usr/bin/python

# BTree - B-tree implementation in Python for didactic purposes.
#
# It includes algorithms to add, search and delete values from 
# the B-tree. It was inspired by this Wikipedia article:
#         https://en.wikipedia.org/wiki/Btree
#
# This module represents an unit test for the B-tree algorithms.
#
# @copyright: Copyright (c) 2014 Robert Zavalczki, distributed
# under the terms and conditions of the Lesser GNU General 
# Public License version 2.1

import unittest
import random
import BTree


class BTreeTest(unittest.TestCase):
    
    def check_tree(self, tree, values):
        for i in values:
            self.assertTrue(tree.search(i))
        if values:
            self.assertTrue(not tree.search(min(values) - 1))
            self.assertTrue(not tree.search(max(values) + 1))
        if tree.size and values:
            self.assertTrue(tree.min() == min(values))
            self.assertTrue(tree.max() == max(values))

    def fixed_test_1(self, order, node_values=None):
        tree = BTree.BTree(order)
        if node_values is None:
            values = [i for i in range(1, 36, 2)]
            values.extend([i for i in range(100, 200, 13)])
            values.extend([i for i in range(10, 20, 2)])
            values.extend([i for i in range(119, 200, 17)])
        else:
            values = node_values

        for i in values:
            tree.add(i)  
            tree.root.check_valid(tree)

        for i in values[:]:
            tree.delete(i)
            tree.root.check_valid(tree)
            values.remove(i)
            self.check_tree(tree, values)

    def rand_test(self, order, count, seed=None):
        random.seed(seed or 17)
        tree = BTree.BTree(order)        
        values = [random.randint(1000, 9999) for i in range(0, count)]

        for i in values[:]:
            if not tree.add(i):
                values.remove(i)  
            tree.root.check_valid(tree)

        random.shuffle(values)
        for i in values[:]:
            tree.delete(i)
            tree.root.check_valid(tree)
            values.remove(i)
            self.check_tree(tree, values)

    def test_fixed_size2(self):
        self.fixed_test_1(3)

    def test_fixed_size3(self):
        self.fixed_test_1(4)
        lst = [4444, 3625, 1391, 9257, 5453, 9803, 4565, 
               3270, 7259, 2904, 3447, 7400, 5966, 5882]
        self.fixed_test_1(4, lst) 

    def test_fixed_size4(self):
        self.fixed_test_1(5)

    def test_rand1(self):
        for seed in range(120000, 120002):
            for i in range(97, 101):
                self.rand_test(4, i, seed)

    def test_rand2(self):
        for seed in range(120000, 120002):
            for i in range(97, 101):
                self.rand_test(5, i, seed)


    def test_small(self):
        tree = BTree.BTree(3)
        for i in range(1, 8):
            tree.add(i)
            assert(tree.search(i))
        for i in range(1, 8):
            assert(tree.search(i))

        tree.root.check_valid(tree)        
        for i in range(1, 8):
            tree.delete(i)
            tree.root.check_valid(tree)
                                  

if __name__ == '__main__':
    unittest.main()
