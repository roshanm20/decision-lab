#!/usr/bin/env python3
"""Kept so older commands still work. The tool now lives in the package:

    python -m decisionlab cohort transactions.csv
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decisionlab.bi import cohort  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=cohort.__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    cohort.add_arguments(parser)
    raise SystemExit(cohort.run(parser.parse_args()))
