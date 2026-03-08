import os
import re

directories = [
    r'c:\Sistema_acompañamiento_integral\src\templates',
    r'c:\Sistema_acompañamiento_integral\src\static\js'
]

def clean_classes_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    
    # Substitutions for cleaner typography style
    content = content.replace('font-black', 'font-semibold')
    content = content.replace(' uppercase', '')
    content = content.replace(' tracking-widest', '')
    content = content.replace(' tracking-wider', '')
    content = content.replace(' tracking-tight', '')
    content = content.replace(' rounded-none', ' rounded-xl')
    
    # Regex substitutions for arbitrary tracking modifiers
    content = re.sub(r' tracking-\[[^\]]+\]', '', content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

for directory in directories:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html') or file.endswith('.js'):
                clean_classes_in_file(os.path.join(root, file))

print("Typography update complete.")
