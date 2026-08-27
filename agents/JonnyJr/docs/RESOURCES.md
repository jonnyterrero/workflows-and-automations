# Resource Database

## Overview
The JonnyJr resource database (`scripts/resources.json`) contains curated learning resources that are automatically integrated into research and synthesis workflows. Resources are organized by subject and automatically matched based on course codes and keywords.

## Adding Resources

### Structure
```json
{
  "resources": {
    "category": {
      "subcategory": [
        {
          "title": "Resource Name",
          "url": "https://example.com",
          "description": "Brief description of the resource"
        }
      ]
    }
  },
  "courseMappings": {
    "COURSE_CODE": ["category.subcategory"]
  }
}
```

### Example: Adding a New Resource
```json
{
  "resources": {
    "mathematics": {
      "new_topic": [
        {
          "title": "My New Math Resource",
          "url": "https://example.com/math",
          "description": "Great resource for learning advanced math"
        }
      ]
    }
  }
}
```

### Example: Mapping to Course
```json
{
  "courseMappings": {
    "MAP2302": ["mathematics.general", "mathematics.new_topic"]
  }
}
```

## Resource Categories

### Mathematics
- `general`: General math resources (Khan Academy, MIT OCW, etc.)
- `laplace`: Laplace transform resources
- `integration`: Integration techniques and tools
- `rms`: Root mean square calculations

### Physics
- `general`: General physics resources
- `circuits`: Circuit analysis and electronics
- `electromagnetism`: E&M concepts and resources

### Bioengineering
- `general`: General bioengineering resources
- `biomaterials`: Biomaterials science resources
- `physiology`: Human physiology resources
- `circuits`: Circuits for bioengineers
- `medicalDevices`: Medical device regulations and standards

### Chemistry
- `general`: General chemistry resources
- `organic`: Organic chemistry resources
- `physical`: Physical chemistry resources

### Computer Science
- `general`: General CS resources
- `algorithms`: Algorithm and data structure resources
- `machineLearning`: ML and AI resources

### Programming
- `matlab`: MATLAB documentation and resources
- `python`: Python and scientific computing resources
- `typescript`: TypeScript documentation

### Tools
- `calculators`: Online calculators and computational tools
- `reference`: General reference sites (Wikipedia, Google Scholar, etc.)

### Art
- `inspiration`: Art and design inspiration resources

## Course Mappings

Resources are automatically loaded based on:
1. **Course Code Detection**: If you specify a course code (e.g., MAP2302), resources mapped to that course are loaded
2. **Keyword Matching**: Resources matching keywords in your topic are loaded
3. **Subject Category**: Resources from relevant subject categories are included

## Usage in Workflows

### Research Phase
Resources are:
- Included in the Perplexity API prompt for context
- Added to the research report under "Learning Resources"
- Used to enhance the research findings

### Synthesis Phase
Resources are:
- Included in the OpenAI prompt for recommendations
- Added to the synthesis output under "References" and "Learning Resources"
- Used to suggest specific study materials

## Best Practices

1. **Keep URLs Updated**: Regularly check that resources are still accessible
2. **Add Descriptions**: Clear descriptions help the AI understand when to use each resource
3. **Organize by Topic**: Group related resources in subcategories
4. **Update Course Mappings**: When adding new courses, update the mappings
5. **Curate Quality**: Focus on high-quality, authoritative resources

## Adding Your Own Resources

1. Open `scripts/resources.json`
2. Navigate to the appropriate category
3. Add your resource following the structure
4. If course-specific, add to `courseMappings`
5. Test by running a research/synthesis workflow

## Examples

### Adding a YouTube Channel
```json
{
  "title": "3Blue1Brown - Linear Algebra",
  "url": "https://www.youtube.com/c/3blue1brown",
  "description": "Visual explanations of linear algebra concepts"
}
```

### Adding a University Course
```json
{
  "title": "Stanford CS229 - Machine Learning",
  "url": "https://cs229.stanford.edu/",
  "description": "Stanford's machine learning course with lectures and notes"
}
```

### Mapping to Multiple Courses
```json
{
  "courseMappings": {
    "BME3506C": ["physics.circuits", "programming.matlab", "mathematics.rms"],
    "EGM3420C": ["physics.general", "mathematics.general"]
  }
}
```

