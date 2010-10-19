import os
import sys

for p in os.listdir('resources/lib'):
    sys.path.append('resources/lib/%s' % p)

sys.path.append('resources/src')
sys.path.append('resources/test')

print 'All src, test, and libs added to path'
