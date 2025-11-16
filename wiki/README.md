# Multi-Heart-Model Wiki Content

This directory contains the complete wiki content for the Multi-Heart-Model repository.

## 📁 Contents

This wiki includes the following pages:

1. **Home.md** - Main landing page with overview and quick links
2. **Getting-Started.md** - Installation guide and first simulation
3. **Architecture.md** - System architecture and design patterns
4. **API-Reference.md** - Complete API documentation
5. **Examples.md** - Practical code examples and tutorials
6. **Development-Guide.md** - Contributing guidelines and workflows
7. **Organ-Chip-Platform.md** - Drug toxicity screening platform guide
8. **Hardware-Integration.md** - Hardware control system integration
9. **Testing.md** - Testing guide and best practices
10. **FAQ.md** - Frequently asked questions
11. **_Sidebar.md** - Navigation sidebar for GitHub wiki

## 🚀 Uploading to GitHub Wiki

GitHub wikis are managed as separate git repositories. Follow these steps to upload this content:

### Method 1: Via GitHub Web Interface

1. Go to your repository on GitHub
2. Click the "Wiki" tab
3. If the wiki doesn't exist, click "Create the first page"
4. For each wiki page:
   - Click "New Page"
   - Set the page title (e.g., "Getting Started")
   - Copy the content from the corresponding `.md` file
   - Click "Save Page"

### Method 2: Via Git Clone (Recommended)

1. **Clone the wiki repository**:
   ```bash
   git clone https://github.com/STLNFTART/Multi-Heart-Model.wiki.git
   cd Multi-Heart-Model.wiki
   ```

2. **Copy wiki files**:
   ```bash
   cp /path/to/Multi-Heart-Model/wiki/*.md .
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add comprehensive wiki documentation"
   git push origin master
   ```

4. **View on GitHub**:
   Navigate to `https://github.com/STLNFTART/Multi-Heart-Model/wiki`

### Method 3: Using this Script

Run from the repository root:

```bash
#!/bin/bash
# upload_wiki.sh

# Clone wiki repo
cd /tmp
git clone https://github.com/STLNFTART/Multi-Heart-Model.wiki.git
cd Multi-Heart-Model.wiki

# Copy wiki content
cp /path/to/Multi-Heart-Model/wiki/*.md .

# Remove README (not needed in wiki)
rm README.md

# Commit and push
git add .
git commit -m "Update wiki with comprehensive documentation"
git push origin master

echo "Wiki updated successfully!"
echo "View at: https://github.com/STLNFTART/Multi-Heart-Model/wiki"
```

## 📝 Maintaining the Wiki

### Updating Existing Pages

1. Clone the wiki repository
2. Edit the relevant `.md` files
3. Commit and push changes
4. Changes appear immediately on GitHub

### Adding New Pages

1. Create new `.md` file in wiki directory
2. Add link to `_Sidebar.md` for navigation
3. Commit and push

### Linking Between Pages

Use relative links without `.md` extension:
```markdown
See the [API Reference](API-Reference) for details.
```

## 🎨 Wiki Structure

### Home Page
Entry point with overview and navigation to all sections.

### Getting Started
New user onboarding:
- Installation
- First simulation
- Basic examples
- Troubleshooting

### Technical Documentation
- **Architecture**: System design and patterns
- **API Reference**: Complete API docs
- **Examples**: Practical code examples

### Specialized Topics
- **Organ-Chip Platform**: Drug toxicity screening
- **Hardware Integration**: Control systems

### Development Resources
- **Development Guide**: Contributing workflow
- **Testing**: Testing strategies and tools

### Support
- **FAQ**: Common questions and solutions

## 🔍 Search

GitHub wiki includes built-in search. Users can search all wiki pages from the search box.

## 📱 Navigation

The `_Sidebar.md` file creates a navigation sidebar on all wiki pages for easy navigation.

## ✨ Best Practices

1. **Keep pages focused**: Each page should cover one topic
2. **Use clear headings**: Help readers scan content
3. **Include examples**: Show, don't just tell
4. **Link generously**: Connect related content
5. **Update regularly**: Keep information current
6. **Test links**: Ensure all internal links work

## 🔗 External Resources

- [GitHub Wiki Documentation](https://docs.github.com/en/communities/documenting-your-project-with-wikis)
- [Markdown Guide](https://www.markdownguide.org/)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)

---

**Last Updated**: 2025-11-16
**Maintainer**: Multi-Heart-Model Team
