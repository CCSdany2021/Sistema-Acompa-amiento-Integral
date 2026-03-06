import re
import os

file_path = r'c:\Sistema_acompañamiento_integral\src\templates\report_detail.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace any rounded class with rounded-none
# This covers rounded, rounded-sm, rounded-md, rounded-lg, rounded-xl, rounded-2xl, rounded-3xl, rounded-full
# And also specific corners like rounded-t-xl, rounded-b-xl, etc.
processed = re.sub(r'rounded-(?:[a-z0-9-]+|none|full)', 'rounded-none', content)
processed = re.sub(r'rounded(?!\-)', 'rounded-none', processed)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(processed)

print("Replacement complete.")
