# JonnyJr - AI Research Repository

[![CI](https://github.com/jonnyterrero/JonnyJr/workflows/Rules%20CI/badge.svg)](https://github.com/jonnyterrero/JonnyJr/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](https://github.com/jonnyterrero/JonnyJr)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-blue)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow)](https://python.org)
[![MATLAB](https://img.shields.io/badge/MATLAB-R2023a-orange)](https://mathworks.com)

An automated AI research repository with intelligent synthesis and reporting capabilities. This system conducts research, synthesizes findings, and automatically creates pull requests for review.

## 🚀 Features

- **Automated Research**: AI-powered research scripts that generate insights and findings
- **Intelligent Synthesis**: Automated synthesis of research data into actionable reports
- **GitHub Integration**: Automatic pull request creation and workflow management
- **Scheduled Workflows**: Daily and weekly automated research cycles
- **Comprehensive Testing**: Full test suite with unit and integration tests
- **Auto-push**: Automatic GitHub synchronization for all changes

## 📁 Project Structure

```
ai-research-repo/
├── .github/
│    └── workflows/
│         ├── ai-research.yml      # Daily research workflow
│         └── nightly-research.yml # Nightly synthesis workflow
├── scripts/
│    ├── research.ts              # Main research script
│    ├── synthesize.ts            # Research synthesis script
│    └── open_pr.ts               # PR creation script
├── .cursor/
│    └── rules/
│         ├── 00-style.md         # Code style guidelines
│         └── 10-testing.md       # Testing guidelines
├── docs/
│    └── nightly/                 # Archived research reports
├── package.json                  # Dependencies and scripts
├── README.md                     # This file
├── RESEARCH.md                   # Generated research findings
├── SYNTHESIS.md                  # Generated synthesis reports
├── auto-push.ps1                # PowerShell auto-push script
└── auto-push.bat                 # Windows batch auto-push script
```

## 🛠️ Setup

### Prerequisites
- Node.js 18+ 
- npm 8+
- Git
- GitHub CLI (for PR management)

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone <your-repo-url>
   cd ai-research-repo
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   # Create .env file
   echo "GITHUB_TOKEN=your_github_token" > .env
   echo "GITHUB_REPOSITORY_OWNER=your_username" >> .env
   ```

3. **Configure GitHub remote:**
   ```bash
   git remote add origin https://github.com/yourusername/ai-research-repo.git
   git push -u origin main
   ```

## 🚀 Usage

### Manual Research Workflow

```bash
# Run research script
npm run research

# Synthesize findings
npm run synthesize

# Create pull request
npm run open-pr
```

### Automated Workflows

The repository includes GitHub Actions workflows that run automatically:

- **Daily Research** (9 AM UTC, Mon-Fri): Conducts research and updates findings
- **Nightly Synthesis** (2 AM UTC daily): Synthesizes research and archives reports

### Auto-push Scripts

For immediate synchronization:

```powershell
# PowerShell
.\auto-push.ps1

# Windows Batch
auto-push.bat
```

## 🧪 Testing

```bash
# Run all tests
npm test

# Run unit tests
npm run test:unit

# Run integration tests
npm run test:integration

# Run with coverage
npm run test:coverage
```

## 📊 Generated Reports

- **RESEARCH.md**: Current research findings and insights
- **SYNTHESIS.md**: Synthesized analysis of research patterns
- **docs/nightly/**: Archived research reports by date

## 🔧 Development

### Code Style
- Follow TypeScript best practices
- Use meaningful variable names
- Include comprehensive error handling
- Write tests for all public APIs

### Testing Guidelines
- Unit tests for individual functions
- Integration tests for workflows
- Mock external dependencies
- Test edge cases and error conditions

## 🤖 AI Research Features

- **Automated Research Topics**: AI-generated research areas and priorities
- **Intelligent Insights**: Pattern recognition in research data
- **Strategic Recommendations**: AI-powered next steps and priorities
- **Cross-Reference Analysis**: Historical research comparison
- **Performance Metrics**: Research impact and effectiveness tracking

## 📈 Workflow Automation

1. **Research Phase**: Automated data collection and analysis
2. **Synthesis Phase**: Pattern recognition and insight generation
3. **Reporting Phase**: Comprehensive report generation
4. **Review Phase**: Automatic PR creation for human review
5. **Archive Phase**: Historical data preservation

## 🎯 Key Benefits

- **Automated Research**: Continuous AI research without manual intervention
- **Intelligent Synthesis**: AI-powered analysis of research patterns
- **GitHub Integration**: Seamless workflow with version control
- **Scalable Architecture**: Easy to extend with new research capabilities
- **Comprehensive Testing**: Reliable and maintainable codebase

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

*This repository is designed for automated AI research with intelligent synthesis and reporting capabilities. All changes are automatically pushed to GitHub for seamless collaboration.* 🚀
