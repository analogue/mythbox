import os
import sys

for p in os.listdir('resources/lib'):
    sys.path.append('resources/lib/%s' % p)

