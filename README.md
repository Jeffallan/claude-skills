# Fullstack Dev Skills Plugin

A comprehensive Claude Code plugin with 19 specialized skills for full-stack developers working with TypeScript, Python, Go, React, React Native, and Flutter.

## Included Skills

### Original Development Skills (6)
1. **DevOps Engineer** - CI/CD, deployment, infrastructure management
2. **Feature Forge** - Requirements gathering and specification creation
3. **Fullstack Guardian** - Full-stack implementation across frontend, backend, and security
4. **Spec Miner** - Code analysis and reverse engineering (read-only)
5. **Test Master** - Comprehensive testing (functional, performance, security)
6. **Code Documenter** - Inline documentation and OpenAPI specs

### Testing & E2E (1)
7. **Playwright Expert** - End-to-end browser testing with Playwright

### Backend Framework Skills (3)
8. **NestJS Expert** - TypeScript backend with NestJS
9. **Django Expert** - Python web framework with Django/DRF
10. **FastAPI Expert** - Async Python APIs with FastAPI

### Frontend & Mobile Skills (3)
11. **React Expert** - Modern React with hooks and TypeScript
12. **React Native Expert** - Cross-platform mobile with React Native
13. **Flutter Expert** - Cross-platform mobile with Flutter/Dart

### Workflow Skills (4)
14. **Debugging Wizard** - Systematic debugging across all languages
15. **Monitoring Expert** - Observability, logging, metrics, alerting
16. **Architecture Designer** - System design and architectural decisions
17. **Code Reviewer** - Comprehensive code review

### Security Skills (2)
18. **Secure Code Guardian** - Writing secure code, preventing vulnerabilities
19. **Security Reviewer** - Security code review and static analysis

## Installation

### Option 1: Install from GitHub (Recommended)

Once this plugin is published to GitHub, install it using Claude Code's plugin system:

```bash
# In Claude Code, add the marketplace
/plugin marketplace add jeffallan/claude-skills

# Install the plugin
/plugin install fullstack-dev-skills@jeffallan

# Restart Claude Code when prompted
```

### Option 2: Install from Local Directory (Development/Testing)

For local development or testing before publishing:

```bash
# In Claude Code, add your local repository as a marketplace
/plugin marketplace add /path/to/claude-skills

# Install the plugin
/plugin install fullstack-dev-skills@local

# Restart Claude Code when prompted
```

### Option 3: Install Skills Directly (Without Plugin System)

Copy skills directly to your global skills directory:
```bash
cp -r ~/projects/claude-skills/skills/* ~/.claude/skills/
```
Then restart Claude Code.

**Note**: This method installs skills but bypasses the plugin management system.

#### For Authors (Publishing as a Plugin)

If you want to publish this plugin to GitHub for others to use, follow these steps:

##### Step 1: Initialize Git Repository
```bash
cd ~/fullstack-dev-skills-plugin

# Initialize git repository
git init

# Create .gitignore
cat > .gitignore << 'GITIGNORE'
# Node modules (if you add any dependencies)
node_modules/

# OS files
.DS_Store
Thumbs.db

# Editor files
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
GITIGNORE

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: Fullstack Dev Skills Plugin v1.0.0"
```

##### Step 2: Create GitHub Repository
1. Go to [GitHub](https://github.com) and create a new repository
2. Name it: `fullstack-dev-skills-plugin` (or your preferred name)
3. **Do NOT initialize with README, .gitignore, or license** (we already have these)
4. Make it **Public** (required for Claude Code plugin distribution)

##### Step 3: Push to GitHub
```bash
# Add remote origin (replace jeffallan with your GitHub username)
git remote add origin https://github.com/jeffallan/claude-skills.git

# Push to GitHub
git branch -M main
git push -u origin main
```

##### Step 4: Create a Release (Recommended)
Creating releases makes it easier for users to install specific versions:

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `Fullstack Dev Skills Plugin v1.0.0`
5. Description:
   ```markdown
   ## Fullstack Dev Skills Plugin v1.0.0
   
   Comprehensive Claude Code plugin with 19 specialized skills for full-stack development.
   
   ### Installation
   ```
   claude plugin install https://github.com/jeffallan/claude-skills
   ```
   
   ### Included Skills
   - 6 Original Development Skills (DevOps, Feature Forge, Fullstack Guardian, etc.)
   - 3 Backend Framework Skills (NestJS, Django, FastAPI)
   - 3 Frontend/Mobile Skills (React, React Native, Flutter)
   - 4 Workflow Skills (Debugging, Monitoring, Architecture, Code Review)
   - 2 Security Skills (Secure Code Guardian, Security Reviewer)
   - 1 Testing Skill (Playwright Expert)
   
   ### Tech Stack Coverage
   TypeScript, Python, Dart, Go, React, React Native, Flutter, NestJS, Django, FastAPI
   ```
6. Click "Publish release"

##### Step 5: Update package.json with Repository Info
```bash
cd ~/fullstack-dev-skills-plugin

# Update package.json with repository information
cat > package.json << 'PACKAGEJSON'
{
  "name": "fullstack-dev-skills",
  "version": "1.0.0",
  "description": "Comprehensive skill pack for full-stack developers covering frameworks, workflows, and security",
  "keywords": [
    "claude-code-plugin",
    "skills",
    "fullstack",
    "typescript",
    "python",
    "react",
    "nestjs",
    "django",
    "fastapi",
    "flutter",
    "react-native",
    "debugging",
    "security",
    "architecture"
  ],
  "author": "jeffallan",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/jeffallan/claude-skills.git"
  },
  "bugs": {
    "url": "https://github.com/jeffallan/claude-skills/issues"
  },
  "homepage": "https://github.com/jeffallan/claude-skills#readme",
  "claudeCode": {
    "type": "plugin",
    "skills": [
      "devops-engineer",
      "feature-forge",
      "fullstack-guardian",
      "spec-miner",
      "test-master",
      "code-documenter",
      "playwright-expert",
      "nestjs-expert",
      "django-expert",
      "fastapi-expert",
      "react-expert",
      "react-native-expert",
      "flutter-expert",
      "debugging-wizard",
      "monitoring-expert",
      "architecture-designer",
      "code-reviewer",
      "secure-code-guardian",
      "security-reviewer"
    ]
  }
}
PACKAGEJSON

# Commit the update
git add package.json
git commit -m "Add repository information to package.json"
git push
```

##### Step 6: (Optional) Submit to Claude Code Plugin Marketplace
Once published on GitHub, you can submit your plugin to the official Claude Code plugin marketplace:

1. Go to [Claude Code Plugin Marketplace](https://claude.com/claude-code/plugins)
2. Click "Submit Plugin"
3. Provide your GitHub repository URL
4. Fill in plugin details
5. Submit for review

##### Step 7: Share Your Plugin
Share your plugin with others:
```
Installation command:
claude plugin install https://github.com/jeffallan/claude-skills

Or add to README badge:
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blue)](https://github.com/jeffallan/claude-skills)
```

### Option 3: Install from Local Directory (Development)
For local development and testing:
```bash
ln -s ~/fullstack-dev-skills-plugin ~/.claude/plugins/fullstack-dev-skills-plugin
```

## Usage

Skills are automatically activated based on context. For example:
- "Help me implement a NestJS API" → activates NestJS Expert
- "Debug this TypeScript error" → activates Debugging Wizard
- "Review this code for security issues" → activates Security Reviewer
- "Set up monitoring for my app" → activates Monitoring Expert

## Skill Categories

### Framework Expertise
- **Backend**: NestJS, Django, FastAPI
- **Frontend**: React
- **Mobile**: React Native, Flutter

### Development Workflows
- Requirements → Feature Forge
- Implementation → Fullstack Guardian
- Testing → Test Master, Playwright Expert
- Code Review → Code Reviewer
- Debugging → Debugging Wizard
- Documentation → Code Documenter

### DevOps & Operations
- Deployment → DevOps Engineer
- Monitoring → Monitoring Expert
- Architecture → Architecture Designer

### Security
- Secure Coding → Secure Code Guardian
- Security Review → Security Reviewer

## Tech Stack Coverage

- **Languages**: TypeScript, JavaScript, Python, Dart, Go
- **Backend**: NestJS, Django, FastAPI, Express
- **Frontend**: React, React Native, Flutter
- **Testing**: Jest, Playwright, Pytest, React Testing Library
- **Databases**: PostgreSQL, MongoDB, MySQL (via ORMs)
- **DevOps**: Docker, Kubernetes, CI/CD pipelines
- **Monitoring**: Prometheus, Grafana, ELK, DataDog
- **Security**: OWASP Top 10, SAST tools, secure coding practices

## Documentation

- **SKILLS_GUIDE.md** - Quick reference for when to use each skill
- Individual **skills/*/SKILL.md** - Comprehensive guide for each skill

## Updating the Plugin

### For Plugin Authors
```bash
# Make changes to skills
# Update version in package.json
# Commit and push
git add .
git commit -m "Update: description of changes"
git push

# Create new release on GitHub
# Tag with new version number (e.g., v1.1.0)
```

### For Plugin Users
```bash
# Update to latest version
claude plugin update fullstack-dev-skills

# Or manually
cd ~/.claude/plugins/fullstack-dev-skills-plugin
git pull
```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-skill`
3. Make your changes
4. Test thoroughly
5. Commit: `git commit -m "Add: new skill or feature"`
6. Push: `git push origin feature/new-skill`
7. Create a Pull Request

### Adding a New Skill

1. Create skill directory: `skills/my-new-skill/`
2. Create `skills/my-new-skill/SKILL.md` with frontmatter:
   ```markdown
   ---
   name: My New Skill
   description: Description with trigger keywords
   ---
   # Content here
   ```
3. Add to `package.json` claudeCode.skills array
4. Test locally
5. Submit PR

## Versioning

This plugin follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible changes
- **MINOR** version for new features (backward compatible)
- **PATCH** version for bug fixes

## License

MIT License - See LICENSE file for details

## Author

Created for fullstack engineers working across the modern web development stack.

## Support

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/jeffallan/claude-skills/issues)
- **Discussions**: Join discussions on [GitHub Discussions](https://github.com/jeffallan/claude-skills/discussions)

## Changelog

### v1.0.0 (Initial Release)
- 19 comprehensive skills for full-stack development
- Support for TypeScript, Python, Go, Dart
- Framework experts for NestJS, Django, FastAPI, React, React Native, Flutter
- Workflow skills for debugging, monitoring, architecture, code review
- Security skills for secure coding and security review
