import sys
from pathlib import Path

# Add project directories to sys.path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "shipping-verification"))
sys.path.insert(0, str(root_dir / "shipping-verification" / "src"))

from src.dashboard import app
