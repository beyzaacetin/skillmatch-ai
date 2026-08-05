import os
import sys
sys.path.insert(0, os.path.abspath("backend"))
try:
    import main
    print("SUCCESS: main imported successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
