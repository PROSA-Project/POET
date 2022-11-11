import unittest

import utils.utils as SUT
from structures.emax import Emax

class TestSourcePatching(unittest.TestCase):

    def test_single_line(self):
        template = '{  \t   $TEST$ trailing'
        expected = '{  \t   FoO trailing'
        self.assertEqual(SUT.patch(template, '$TEST$', 'FoO'), expected)

    def test_multi_line(self):
        template = '{  \t   $TEST$ trailing'
        expected = '{  \t   FoO\n' + \
                   '   \t   Bar! trailing'
        self.assertEqual(SUT.patch(template, '$TEST$', 'FoO\nBar!'), expected)

class TestPars(unittest.TestCase):

    def test_example(self):
        self.assertEqual(SUT.pars("git commit -m", "initial commit"),
                        ["git", "commit", "-m", "initial", "commit"])

class TestPars(unittest.TestCase):

    def test_example(self):
        working = Emax(10,[[1,1]])
        working = Emax(10,[[1,1],[2,2]])
        working = Emax(21,[[1,9],[10,10],[20,19]])
        
        broken = []
        broken += [[10,[[0,0]]]] # (0,0) in steps
        broken += [[10,[[1,0]]]] # first step contains 0
        broken += [[10,[[1,1],[1,1]]]] # not strictly monotonic
        broken += [[10,[[2,1],[1,4]]]] # not strictly monotonic
        broken += [[5,[[2,1],[7,4]]]] # horizon too small
        broken += [[10,[[1,1],[2,2],[3,10]]]] # not subadditive
        broken += [[40,[[1,1],[20,2],[31,4]]]] # not subadditive
        failed = [False for e in broken]
        for i in range(len(broken)):
            try: 
                e = Emax(broken[i][0], broken[i][1])
            except: 
                failed[i] = True

        assert all(failed)


if __name__ == '__main__':
    unittest.main()
