from typing import List
import requests
import os

class DocumentationAgent:
    def __init__(self, repo_name: str, endpoint: str) -> None:
        self.repo_name = repo_name
        self.endpoint = endpoint
        self.structure = self.get_structure()

    def get_structure(self) -> List:
        try:
            response = requests.get(self.endpoint + "/docs-structure")
            response.raise_for_status()
            return response.json()["result"]["headings"]
        except Exception as e:
            print(e)

    def _fetch_content(self, heading: str, subheading: str) -> str:
        try:
            payload = {
                "heading": heading,
                "subheading": subheading 
            }
            response = requests.get(self.endpoint + "/docs-content", json=payload)
            response.raise_for_status()
            return response.json()["result"]
        except Exception as e:
            print(e)

    # def _upload_documentation() {

    # }
    
    def get_content(self):
        if self.structure:
            for heading in self.structure:
                title = heading["title"]
                # Create a directory for the title if it doesn't exist
                os.makedirs(f"docs/{title}", exist_ok=False)
                for subheading in heading["subheadings"]:
                    response = self._fetch_content(heading=title, subheading=subheading)
                    print(response)
                    # Save each subheading content in a separate markdown file
                    with open(f"docs/{title}/{subheading}.md", "w") as md_file:
                        md_file.write(
f"""---
id: {title}.{subheading}
title: {subheading}
---
""")
                        md_file.write(f"# {subheading}\n")
                        md_file.write(f"{response}\n")

            # self._upload_documentation()

if __name__ == "__main__":
    doc = DocumentationAgent("blorm-network-ZerePy", "http://localhost:8000/blorm-network-ZerePy")
    doc.get_content()
                    