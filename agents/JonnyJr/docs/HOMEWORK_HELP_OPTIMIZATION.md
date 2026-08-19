# Homework Help Optimization

## Overview
The homework help workflow has been optimized to recognize your specific courses and provide tailored assistance for bioengineering, chemistry, computer science, mathematics, and physics coursework.

## What's New

### 1. Course Configuration (`scripts/courses.json`)
- **Course Database**: Complete metadata for all your current and upcoming courses
- **Current Courses** (Summer 2025):
  - `MAP2302` - Differential Equations
  - `PHY2049` - General Physics II with Lab
- **Upcoming Courses** (Fall 2025):
  - `BME3100C` - Introduction to Biomaterials
  - `BME3404C` - Human Physiology for Engineers II
  - `BME3506C` - Circuits for Bioengineers
  - `BME4722` - Health Care Engineering

### 2. Course Detection
- **Automatic Recognition**: Detects course codes (e.g., MAP2302, BME3100C) from input
- **Keyword Matching**: Falls back to keyword matching if course code not detected
- **Context-Aware**: Uses course-specific knowledge for better results

### 3. Enhanced Research Prompts
- **Course-Specific Context**: Research prompts include course information, textbooks, and tools
- **Subject-Aware**: Tailored prompts for bioengineering, math, physics, etc.
- **Practical Focus**: Emphasis on solving homework problems, not just general research

### 4. Course-Specific Synthesis
- **Subject Templates**: Different synthesis formats for different subjects
  - **Math**: Step-by-step problem solving, formula references, verification methods
  - **Physics**: Diagrams, unit checks, fundamental principles
  - **Bioengineering**: Engineering + biological perspectives, regulatory considerations
- **Tool Recommendations**: Suggests appropriate tools (MATLAB, Python, etc.) based on course
- **Textbook References**: Includes relevant textbook citations

### 5. Organized File Structure
- **Automatic Organization**: Files saved to `school/<COURSE>/<assignment>/`
- **README Generation**: Auto-creates README.md in assignment directory
- **Clean Structure**: No more files cluttering the root directory

## Usage

### Via GitHub Actions
1. Go to **Actions** → **Homework Help**
2. Click **Run workflow**
3. Fill in:
   - **Course**: e.g., `MAP2302`, `BME3100C`
   - **Assignment**: e.g., `HW1 - Laplace Transforms`
   - **Category**: Select appropriate category
4. Review the generated PR with research and synthesis

### Via Command Line
```bash
# Research
npx ts-node scripts/research.ts "MAP2302 HW1 Laplace transforms"

# Synthesize
npx ts-node scripts/synthesize.ts RESEARCH.md
```

## File Structure
```
school/
├── MAP2302/
│   └── hw1-laplace/
│       ├── README.md      # Assignment overview
│       ├── RESEARCH.md    # Research findings
│       └── SYNTHESIS.md   # Actionable plan
├── BME3100C/
│   └── assignment-name/
│       └── ...
└── ...
```

## Course-Specific Features

### Mathematics (MAP2302, MAC2313)
- Step-by-step solution approaches
- Formula references and verification methods
- MATLAB/Python verification strategies
- Common algebraic pitfalls

### Physics (PHY2049)
- Diagram creation guidance
- Unit consistency checks
- Fundamental principle application
- Numerical verification methods

### Bioengineering (BME courses)
- Dual perspective (engineering + biological)
- Regulatory and safety considerations
- Material selection guidance
- Practical application focus

### Computer Science (Self-study)
- Algorithm and data structure guidance
- Code examples and patterns
- Best practices and optimization

## Customization

### Adding New Courses
Edit `scripts/courses.json` and add your course:
```json
{
  "courses": {
    "NEWCOURSE": {
      "name": "Course Name",
      "subject": "Subject",
      "credits": 3,
      "current": true,
      "term": "Fall 2025",
      "category": "Sciences",
      "keywords": ["keyword1", "keyword2"],
      "commonTopics": ["Topic 1", "Topic 2"],
      "textbooks": ["Textbook 1"],
      "tools": ["MATLAB", "Python"],
      "typicalAssignments": ["Assignment type"]
    }
  }
}
```

### Updating Course Info
Modify the course entry in `scripts/courses.json` to update:
- Current/upcoming status
- Term information
- Keywords for better detection
- Tools and textbooks

## Resource Integration

### Curated Resource Database (`scripts/resources.json`)
The system now includes a comprehensive database of learning resources organized by subject:

- **Mathematics**: Khan Academy, Paul's Online Notes, Wolfram MathWorld, MIT OCW
- **Physics**: HyperPhysics, circuit simulators, E&M resources
- **Bioengineering**: MIT OCW, PubMed, FDA resources, medical device standards
- **Chemistry**: Organic chemistry portals, physical chemistry resources
- **Computer Science**: Visualgo, LeetCode, ML courses
- **Programming**: MATLAB/Python documentation, official guides
- **Tools**: Calculators, reference sites, academic databases

### Automatic Resource Matching
- **Course-Based**: Resources automatically matched to your courses
- **Topic-Based**: Resources matched based on keywords in your assignment
- **Integrated Output**: Resources included in both research and synthesis outputs

### Example Resource Categories
- **MAP2302**: Laplace transforms, integration techniques, MATLAB resources
- **PHY2049**: Circuit analysis, electromagnetism, RMS calculations
- **BME Courses**: Biomaterials databases, physiology resources, medical device regulations

## Benefits

1. **Better Research**: Course-specific context leads to more relevant research
2. **Targeted Help**: Synthesis tailored to your subject and assignment type
3. **Organized Workflow**: Files automatically organized by course and assignment
4. **Consistency**: Same structure across all assignments
5. **Efficiency**: Less manual organization, more focus on learning
6. **Resource Discovery**: Automatically surfaces relevant learning resources alongside API research
7. **Comprehensive Help**: Combines AI research (Perplexity/OpenAI) with curated educational resources

## Next Steps

- Add more courses as you progress through your program
- Customize keywords and topics based on actual coursework
- Update tools and textbooks as instructors specify
- Share feedback on what works best for your learning style

