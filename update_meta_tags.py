import os
import re

def add_meta_tag(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check if meta tag already exists
    if 'google-site-verification' in content:
        print(f"Skipping {file_path} - already has verification meta tag")
        return False
    
    # Add meta tag after the first <head> tag
    new_content = content.replace(
        '<head>', 
        '<head>\n    <meta name="google-site-verification" content="w2tVvd9upM2GXkKphEKtZG5DmJg7UMNSsO7fvCDwHow" />',
        1
    )
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Updated {file_path}")
        return True
    return False

def main():
    templates_dir = os.path.join('d:\\', 'Health_Food_Monitor', 'templates')
    updated_files = []
    
    # Process all HTML files in the templates directory
    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html') and file != 'google806a72d7c04e86eb.html':
                file_path = os.path.join(root, file)
                if add_meta_tag(file_path):
                    updated_files.append(file_path)
    
    print("\nUpdated files:")
    for file in updated_files:
        print(f"- {file}")

if __name__ == "__main__":
    main()
