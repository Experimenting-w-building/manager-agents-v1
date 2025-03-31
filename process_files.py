import os
import json
import shutil
import argparse
from pathlib import Path

def process_documentation(source_dir, docs_dir='docs'):
    """
    Process markdown files from source directory to Docusaurus-ready format
    - Copies Markdown files
    - Adds front matter where missing
    - Creates directory structure
    """
    print(f"Processing documentation from {source_dir} to {docs_dir}")
    
    # Clear existing docs directory
    if os.path.exists(docs_dir):
        shutil.rmtree(docs_dir)
    os.makedirs(docs_dir, exist_ok=True)

    # Process markdown files
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.md'):
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, source_dir)
                dest_path = os.path.join(docs_dir, rel_path)

                # Create target directory
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                # Process file content
                with open(src_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Generate front matter if missing
                if not content.startswith('---'):
                    file_name = Path(file).stem
                    front_matter = f"""---
id: {file_name}
title: {file_name.replace('-', ' ').title()}
---\n\n"""
                    content = front_matter + content

                # Write processed file
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    print(f"Processed: {rel_path}")

def generate_sidebar(docs_dir='docs', sidebar_path='sidebars.js'):
    """
    Generate Docusaurus sidebar configuration from directory structure
    """
    print("Generating sidebar configuration...")
    
    sidebar = {}
    
    for root, dirs, files in os.walk(docs_dir):
        # Skip root directory
        if root == docs_dir:
            category = "Documentation"
        else:
            category = os.path.relpath(root, docs_dir).replace(os.path.sep, ' / ').title()
        
        items = []
        for f in files:
            if f.endswith('.md') and not f.startswith('_'):
                # Convert file path to Docusaurus ID format
                file_path = os.path.relpath(os.path.join(root, f), docs_dir)
                doc_id = os.path.splitext(file_path)[0].replace(os.path.sep, '/')
                items.append(doc_id)
        
        if items:
            sidebar[category] = items

    # Write sidebar configuration
    with open(sidebar_path, 'w', encoding='utf-8') as f:
        f.write("module.exports = {\n")
        f.write("  docsSidebar: {\n")
        for category, items in sidebar.items():
            f.write(f'    "{category}": [\n')
            for item in items:
                f.write(f'      "{item}",\n')
            f.write("    ],\n")
        f.write("  },\n};\n")
    print(f"Generated sidebar configuration at {sidebar_path}")

def setup_github_actions():
    """
    Create GitHub Actions deployment workflow
    """
    workflow_dir = '.github/workflows'
    os.makedirs(workflow_dir, exist_ok=True)
    
    workflow_content = f"""name: Deploy Documentation

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install Dependencies
        run: npm install

      - name: Process Documentation
        run: python process_docs.py --source existing_docs

      - name: Build Documentation
        run: npm run build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{{{ secrets.GITHUB_TOKEN }}}}
          publish_dir: ./build
"""

    workflow_path = os.path.join(workflow_dir, 'deploy.yml')
    with open(workflow_path, 'w', encoding='utf-8') as f:
        f.write(workflow_content)
    print(f"Created GitHub Actions workflow at {workflow_path}")

def main():
    parser = argparse.ArgumentParser(description='Prepare documentation for Docusaurus')
    parser.add_argument('--source', default='existing_docs', 
                      help='Source directory containing markdown files')
    parser.add_argument('--docs', default='docs',
                      help='Target directory for processed documentation')
    args = parser.parse_args()

    # Process documentation
    process_documentation(args.source, args.docs)
    
    # Generate sidebar
    generate_sidebar(args.docs)
    
    # Setup GitHub Actions
    setup_github_actions()
    
    print("\nSetup complete! Next steps:")
    print("1. Run 'npm install' to install Docusaurus dependencies")
    print("2. Run 'npm start' to view documentation locally")
    print("3. Commit and push to GitHub")
    print("4. Enable GitHub Pages in repository settings")

if __name__ == '__main__':
    main()