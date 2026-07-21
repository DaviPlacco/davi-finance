import os
import glob

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Fix hidden buttons on mobile (make them visible below lg screens)
    content = content.replace('opacity-0 group-hover:opacity-100', 'opacity-100 lg:opacity-0 lg:group-hover:opacity-100')
    
    # Add active state for cards with hover translation
    content = content.replace('hover:-translate-y-1', 'hover:-translate-y-1 active:scale-[0.98]')

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")

for root, dirs, files in os.walk('/Users/daviplacco/Documents/Davi Finance/frontend/src/app/dashboard'):
    for file in files:
        if file.endswith('.tsx'):
            process_file(os.path.join(root, file))

