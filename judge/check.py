"""check_missing_files — pre-judge existence check.

Before calling the judge, every path in file_paths must exist. Any missing path
→ caller sets score=0 and skips the judge call entirely. A trailing "*" means
"this is a directory"; it is checked with os.path.isdir.
"""

import os


def check_missing_files(file_paths):
    """Return the subset of file_paths that do not exist.

    Args:
        file_paths: list[str]. A path ending in "*" is treated as a directory
            (the "*" is stripped and os.path.isdir is used). Otherwise
            os.path.exists is used.

    Returns:
        list[str]: the missing paths (empty if all present).
    """
    missing = []
    for fp in file_paths:
        if fp.endswith("*"):
            if not os.path.isdir(fp[:-1]):
                missing.append(fp)
        else:
            if not os.path.exists(fp):
                missing.append(fp)
    return missing
