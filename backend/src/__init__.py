import os
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Add the src directory to the Python path
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)