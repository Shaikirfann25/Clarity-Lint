import sys
from pathlib import Path

# Add project root to sys.path for test discovery
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_configure(config):
    """Register custom markers to suppress PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers",
        "requires_checkpoint: mark test as requiring the trained DistilBERT checkpoint "
        "in models/distilbert_clarity_lint/"
    )
