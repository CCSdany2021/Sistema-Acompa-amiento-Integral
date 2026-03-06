import os
import sys

print(f"Filesystem encoding: {sys.getfilesystemencoding()}")
print(f"Default encoding: {sys.getdefaultencoding()}")

print("\nEnvironment Variables:")
for k, v in os.environ.items():
    if k == 'DATABASE_URL':
        print(f"{k}: {v}")
    # check for suspicious characters
    try:
        k.encode('utf-8')
        v.encode('utf-8')
    except UnicodeEncodeError:
        print(f"Warning: {k} or its value has confusing/non-utf-8 chars")

import src.config
print(f"\nConfig DATABASE_URL: {src.config.settings.DATABASE_URL}")
