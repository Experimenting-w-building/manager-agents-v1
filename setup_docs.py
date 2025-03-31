import os
import json
import shutil
import argparse
import subprocess
from pathlib import Path
import sys
from sys import exit

# ASCII color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def check_prerequisites():
    """Verify required tools are installed"""
    print(f"{YELLOW}🔍 Checking prerequisites...{RESET}")
    
    # Check Node.js/npm
    try:
        subprocess.run(["node", "-v"], check=True, capture_output=True)
        subprocess.run(["npm", "-v"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{YELLOW}❌ Error: Node.js and npm are required but not found!{RESET}")
        print(f"{YELLOW}Install from https://nodejs.org/ and try again{RESET}")
        exit(1)

    # Check Python version
    if not (3, 6) <= (sys.version_info.major, sys.version_info.minor):
        print(f"{YELLOW}❌ Error: Python 3.6 or higher is required{RESET}")
        exit(1)

    print(f"{GREEN}✅ All prerequisites met{RESET}")

def create_docusaurus_app(project_name, template="classic"):
    """Create new Docusaurus project"""
    print(f"{YELLOW}🚀 Creating Docusaurus app '{project_name}'...{RESET}")
    
    try:
        subprocess.run(
            ["npx", "create-docusaurus@latest", project_name, template, "--javascript"],
            check=True,
            stdout=subprocess.DEVNULL
        )
        os.chdir(project_name)
        print(f"{GREEN}✅ Docusaurus app created{RESET}")
        return True
    except subprocess.CalledProcessError:
        print(f"{YELLOW}❌ Failed to create Docusaurus app{RESET}")
        return False

def install_dependencies():
    """Install npm packages"""
    print(f"{YELLOW}📦 Installing dependencies...{RESET}")
    try:
        subprocess.run(["npm", "install"], check=True)
        print(f"{GREEN}✅ Dependencies installed{RESET}")
        return True
    except subprocess.CalledProcessError:
        print(f"{YELLOW}❌ Failed to install dependencies{RESET}")
        return False

def process_documentation(source_dir, docs_dir='docs'):
    """Process markdown files into Docusaurus format"""
    print(f"{YELLOW}📄 Processing documentation from {source_dir}...{RESET}")
    
    if not os.path.exists(source_dir):
        print(f"{YELLOW}❌ Source directory {source_dir} not found{RESET}")
        return False

    try:
        if os.path.exists(docs_dir):
            shutil.rmtree(docs_dir)
        shutil.copytree(source_dir, docs_dir, ignore=shutil.ignore_patterns('.*'))
        
        # Add front matter to all markdown files
        for root, _, files in os.walk(docs_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r+', encoding='utf-8') as f:
                        content = f.read()
                        if not content.startswith('---'):
                            f.seek(0)
                            f.write(f"---\nid: {Path(file).stem}\ntitle: {Path(file).stem.replace('-', ' ').title()}\n---\n\n{content}")
        print(f"{GREEN}✅ Documentation processed{RESET}")
        return True
    except Exception as e:
        print(f"{YELLOW}❌ Error processing docs: {e}{RESET}")
        return False

def generate_sidebar(docs_dir='docs'):
    """Generate sidebar configuration"""
    print(f"{YELLOW}📚 Generating sidebar...{RESET}")
    
    try:
        sidebar = {"docsSidebar": []}
        
        for root, dirs, files in os.walk(docs_dir):
            current_dir = os.path.relpath(root, docs_dir)
            if current_dir == ".":
                category = "Getting Started"
            else:
                category = current_dir.replace('-', ' ').title()
            
            items = []
            for file in sorted(files):
                if file.endswith('.md') and not file.startswith('_'):
                    doc_id = os.path.join(current_dir, file).replace('\\', '/').replace('.md', '')
                    items.append(doc_id)
            
            if items:
                sidebar["tutorialSideBar"].append({
                    "type": "category",
                    "label": category,
                    "items": items
                })

        with open('sidebars.js', 'w', encoding='utf-8') as f:
            f.write("module.exports = ")
            json.dump(sidebar, f, indent=2)
            f.write(";\n")
        
        print(f"{GREEN}✅ Sidebar generated{RESET}")
        return True
    except Exception as e:
        print(f"{YELLOW}❌ Error generating sidebar: {e}{RESET}")
        return False

def setup_github_pages():
    """Configure GitHub Pages deployment"""
    print(f"{YELLOW}⚙️ Setting up GitHub Pages...{RESET}")
    
    try:
        os.makedirs(".github/workflows", exist_ok=True)
        workflow_content = f"""name: Deploy Documentation

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run build
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{{{ secrets.GITHUB_TOKEN }}}}
          publish_dir: ./build
"""
        with open(".github/workflows/deploy.yml", "w") as f:
            f.write(workflow_content)
        
        print(f"{GREEN}✅ GitHub Pages workflow created{RESET}")
        return True
    except Exception as e:
        print(f"{YELLOW}❌ Error setting up GitHub Pages: {e}{RESET}")
        return False

def update_docusaurus_config(project_name):
    """Update docusaurus.config.js to set onBrokenLinks to 'warn' and baseUrl to '/projectName/'"""
    print(f"{YELLOW}⚙️ Updating Docusaurus configuration...{RESET}")
    
    config_path = 'docusaurus.config.js'
    if not os.path.exists(config_path):
        print(f"{YELLOW}❌ Config file {config_path} not found{RESET}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # Check if onBrokenLinks is already set to 'warn'
        if "onBrokenLinks: 'warn'" in config_content or 'onBrokenLinks: "warn"' in config_content:
            print(f"{GREEN}✅ onBrokenLinks already set to 'warn'{RESET}")
        else:
            # Replace onBrokenLinks with 'warn'
            if "onBrokenLinks:" in config_content:
                config_content = config_content.replace(
                    "onBrokenLinks: 'throw'", "onBrokenLinks: 'warn'"
                ).replace(
                    'onBrokenLinks: "throw"', 'onBrokenLinks: "warn"'
                )
            else:
                # If onBrokenLinks is not found, add it after projectName
                config_content = config_content.replace(
                    "projectName: 'docusaurus',", 
                    "projectName: 'docusaurus',\n\n  onBrokenLinks: 'warn',"
                )
            print(f"{GREEN}✅ Updated onBrokenLinks to 'warn'{RESET}")
        
        # Update baseUrl to match project name
        project_name = project_name
        if "baseUrl: '/'" in config_content or 'baseUrl: "/"' in config_content:
            config_content = config_content.replace(
                "baseUrl: '/'", f"baseUrl: '/{project_name}/'"
            ).replace(
                'baseUrl: "/"', f'baseUrl: "/{project_name}/"'
            )
            print(f"{GREEN}✅ Updated baseUrl to '/{project_name}/'{RESET}")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return True
    except Exception as e:
        print(f"{YELLOW}❌ Error updating Docusaurus config: {e}{RESET}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Full Docusaurus setup automation")
    parser.add_argument("--project", default="my-docs", help="Project directory name")
    parser.add_argument("--source", required=True, help="Path to markdown files")
    parser.add_argument("--template", choices=["classic", "blog"], default="classic",
                      help="Docusaurus template type")
    parser.add_argument("--skip-gh", action="store_true", help="Skip GitHub Pages setup")
    
    args = parser.parse_args()

    check_prerequisites()
    
    if not create_docusaurus_app(args.project, args.template):
        exit(1)
    
    if not install_dependencies():
        exit(1)
    
    if not update_docusaurus_config(args.project):
        exit(1)
    
    if not process_documentation(args.source):
        exit(1)

    # if not generate_sidebar():
    #     exit(1)
    
    if not args.skip_gh and not setup_github_pages():
        exit(1)

    print(f"\n{GREEN}🚀 Setup complete! Next steps:{RESET}")
    print(f"{CYAN}1. Start local server: {RESET}npm start")
    print(f"{CYAN}2. Initialize git repo: {RESET}git init && git add . && git commit -m 'Initial commit'")
    print(f"{CYAN}3. Create GitHub repository and push:{RESET}")
    print(f"   git remote add origin https://github.com/YOUR-USERNAME/{args.project}.git")
    print(f"   git push -u origin main")
    print(f"{CYAN}4. Enable GitHub Pages in repository settings (gh-pages branch){RESET}")

if __name__ == "__main__":
    main()