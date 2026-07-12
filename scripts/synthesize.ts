#!/usr/bin/env node

import fs from "fs";
import { readFileSync, existsSync } from "fs";
import { join } from "path";
import fetch from "node-fetch";

interface SynthesisResult {
  brief: string;
  issues: string[];
  prDescription: string;
  testPlan: string;
}

interface OpenAIResponse {
  choices?: Array<{
    message?: {
      content?: string;
    };
  }>;
}

interface CourseInfo {
  name: string;
  subject: string;
  credits: number;
  current?: boolean;
  upcoming?: boolean;
  term: string;
  category: string;
  keywords: string[];
  commonTopics: string[];
  textbooks: string[];
  tools: string[];
  typicalAssignments: string[];
}

interface CoursesConfig {
  courses: Record<string, CourseInfo>;
  selfStudy: Record<string, {
    topics: string[];
    category: string;
  }>;
}

interface Resource {
  title: string;
  url: string;
  description: string;
}

interface ResourcesConfig {
  resources: Record<string, Record<string, Resource[]>>;
  courseMappings: Record<string, string[]>;
}

class ResearchSynthesizer {
  private inputFile: string;
  private apiKey: string;
  private input: string;
  private coursesConfig: CoursesConfig | null = null;
  private detectedCourse: CourseInfo | null = null;
  private resourcesConfig: ResourcesConfig | null = null;
  private relevantResources: Resource[] = [];

  constructor(inputFile: string = "RESEARCH.md") {
    this.inputFile = inputFile;
    this.apiKey = process.env.OPENAI_API_KEY || '';
    this.input = '';
    this.loadCoursesConfig();
    this.loadResourcesConfig();
  }

  private loadCoursesConfig(): void {
    try {
      const possiblePaths = [
        join(process.cwd(), 'scripts', 'courses.json'),
        join(process.cwd(), 'courses.json')
      ];
      
      let configPath: string | null = null;
      for (const path of possiblePaths) {
        if (existsSync(path)) {
          configPath = path;
          break;
        }
      }
      
      if (configPath) {
        const configContent = readFileSync(configPath, 'utf-8');
        this.coursesConfig = JSON.parse(configContent) as CoursesConfig;
      }
    } catch (error) {
      // Silently fail - course config is optional
    }
  }

  private loadResourcesConfig(): void {
    try {
      const possiblePaths = [
        join(process.cwd(), 'scripts', 'resources.json'),
        join(process.cwd(), 'resources.json')
      ];
      
      let configPath: string | null = null;
      for (const path of possiblePaths) {
        if (existsSync(path)) {
          configPath = path;
          break;
        }
      }
      
      if (configPath) {
        const configContent = readFileSync(configPath, 'utf-8');
        this.resourcesConfig = JSON.parse(configContent) as ResourcesConfig;
      }
    } catch (error) {
      // Silently fail - resources config is optional
    }
  }

  private loadRelevantResources(): void {
    if (!this.resourcesConfig) return;
    
    const resources: Resource[] = [];
    const inputLower = this.input.toLowerCase();
    
    // Load course-specific resources if course detected
    if (this.detectedCourse) {
      const courseCode = Object.keys(this.coursesConfig?.courses || {}).find(
        code => this.coursesConfig?.courses[code] === this.detectedCourse
      );
      
      if (courseCode && this.resourcesConfig.courseMappings[courseCode]) {
        for (const mapping of this.resourcesConfig.courseMappings[courseCode]) {
          const [category, subcategory] = mapping.split('.');
          const categoryResources = this.resourcesConfig.resources[category];
          if (categoryResources && categoryResources[subcategory]) {
            resources.push(...categoryResources[subcategory]);
          }
        }
      }
    }
    
    // Also load topic-based resources
    const topicKeywords = [
      { keywords: ['laplace', 'transform'], paths: ['mathematics.laplace'] },
      { keywords: ['integral', 'integration'], paths: ['mathematics.integration'] },
      { keywords: ['rms', 'root mean square'], paths: ['mathematics.rms'] },
      { keywords: ['circuit', 'electric'], paths: ['physics.circuits', 'bioengineering.circuits'] },
      { keywords: ['biomaterial'], paths: ['bioengineering.biomaterials'] },
      { keywords: ['physiology', 'organ'], paths: ['bioengineering.physiology'] },
      { keywords: ['organic', 'chemistry'], paths: ['chemistry.organic'] },
      { keywords: ['matlab'], paths: ['programming.matlab'] },
      { keywords: ['python'], paths: ['programming.python'] }
    ];
    
    for (const { keywords, paths } of topicKeywords) {
      if (keywords.some(kw => inputLower.includes(kw))) {
        for (const path of paths) {
          const [category, subcategory] = path.split('.');
          const categoryResources = this.resourcesConfig.resources[category];
          if (categoryResources && categoryResources[subcategory]) {
            resources.push(...categoryResources[subcategory]);
          }
        }
      }
    }
    
    // Remove duplicates
    const seenUrls = new Set<string>();
    this.relevantResources = resources.filter(resource => {
      if (seenUrls.has(resource.url)) return false;
      seenUrls.add(resource.url);
      return true;
    });
  }

  private detectCourse(): void {
    if (!this.coursesConfig) return;
    
    const inputUpper = this.input.toUpperCase();
    
    for (const [code, courseInfo] of Object.entries(this.coursesConfig.courses)) {
      if (inputUpper.includes(code) || inputUpper.includes(code.replace(/\d+/g, ''))) {
        this.detectedCourse = courseInfo;
        break;
      }
    }
    
    if (!this.detectedCourse) {
      const inputLower = this.input.toLowerCase();
      for (const [code, courseInfo] of Object.entries(this.coursesConfig.courses)) {
        const matchedKeywords = courseInfo.keywords.filter(kw => 
          inputLower.includes(kw.toLowerCase())
        );
        if (matchedKeywords.length >= 2) {
          this.detectedCourse = courseInfo;
          break;
        }
      }
    }
  }

  async loadInput(): Promise<void> {
    console.log(`📚 Loading input from: ${this.inputFile}`);
    
    if (!fs.existsSync(this.inputFile)) {
      throw new Error(`Input file not found: ${this.inputFile}`);
    }
    
    this.input = fs.readFileSync(this.inputFile, 'utf8');
    console.log(`📊 Loaded ${this.input.length} characters from input file`);
    this.detectCourse();
    this.loadRelevantResources();
    
    if (this.detectedCourse) {
      console.log(`🎓 Detected course: ${this.detectedCourse.name}`);
    }
    if (this.relevantResources.length > 0) {
      console.log(`🔗 Loaded ${this.relevantResources.length} relevant resources`);
    }
  }

  async synthesizeWithOpenAI(): Promise<string> {
    if (!this.apiKey) {
      console.warn('⚠️  OPENAI_API_KEY not found. Using simulated synthesis.');
      return this.generateSimulatedSynthesis();
    }

    console.log('🤖 Synthesizing research with OpenAI...');
    console.log(`📊 Input size: ${this.input.length} characters`);
    
    if (this.detectedCourse) {
      console.log(`🎓 Course context: ${this.detectedCourse.name}`);
    }
    
    if (this.relevantResources.length > 0) {
      console.log(`📚 Including ${this.relevantResources.length} relevant resources`);
    }
    
    console.log('⏳ This may take 20-40 seconds...');
    
    const userContext = `You are helping a dedicated bioengineering student (minors: Chemistry & Computer Science) who:
- Self-studies actively and works on multiple projects
- Needs practical, actionable guidance
- Benefits from clear step-by-step instructions
- Appreciates connections between topics
- Values efficiency and clarity`;

    let systemPrompt = `${userContext}\n\nRead the research below and create a concise, actionable plan. Structure your response with these sections (use exactly these headers):`;
    
    if (this.detectedCourse) {
      systemPrompt += `\n\n**Course Context:**
- Course: ${this.detectedCourse.name} (${this.detectedCourse.subject})
- Status: ${this.detectedCourse.current ? 'Currently Enrolled' : this.detectedCourse.upcoming ? 'Upcoming' : 'Past Course'}
- Recommended Tools: ${this.detectedCourse.tools.join(', ')}
- Key Textbooks: ${this.detectedCourse.textbooks.join(', ')}`;
    }

    if (this.relevantResources.length > 0) {
      systemPrompt += `\n\n**Available Learning Resources** (reference these in your recommendations):
${this.relevantResources.slice(0, 10).map(r => `- ${r.title}: ${r.url}\n  ${r.description}`).join('\n')}`;
    }
    
    systemPrompt += `

# Summary
Provide a 2-3 sentence summary of what needs to be done and why it matters.

# Direct Answers
- Answer the core question(s) clearly (3-7 concise bullets)
- Include key formulas, concepts, or facts needed
- For homework: state the problem-solving approach upfront
- For projects: define the MVP or scope
- For art: describe the style and execution approach

# Step-by-Step Action Plan
Create a numbered, actionable checklist (5-10 steps) that the student can follow immediately:
- Each step should be specific and executable
- Include sub-steps for complex actions
- Note which steps require which tools/resources
- Estimate time if helpful (e.g., "Step 1 (10 min): ...")
- For homework: walk through problem-solving process
- For projects: include setup, implementation, and testing steps

# Required Materials & Tools
List everything needed:
${this.detectedCourse ? `- Recommended Tools: ${this.detectedCourse.tools.join(', ')}\n` : ''}- Software/libraries required
- Reference materials
- Data or inputs needed
- Hardware (if applicable)

# Common Pitfalls & How to Avoid
- 3-5 most common mistakes (be specific)
- How to recognize each mistake early
- Prevention strategies
- Quick verification methods to catch errors

# Verification & Testing
- How to verify the solution/approach is correct
- Quick sanity checks
- Testing strategies
- What "done" looks like

# Additional Resources
Reference specific resources from the research:
${this.relevantResources.length > 0 ? `- Primary: ${this.relevantResources.slice(0, 3).map(r => r.title).join(', ')}\n` : ''}${this.detectedCourse ? `- Course Textbook: ${this.detectedCourse.textbooks[0] || 'See research'}\n` : ''}- Practice problems or exercises
- Related topics to explore next

# Next Steps After Completion
What to do after finishing this task:
- Follow-up questions to consider
- Related topics to learn
- How this connects to other coursework
- Optional extensions or improvements

**Output Guidelines:**
- Use clear markdown formatting with proper headers
- Keep each section focused and scannable
- Use bullet points for lists
- Include specific examples where helpful
- Be encouraging but realistic
- Connect to broader learning goals when relevant`;
    
    const body = {
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content: systemPrompt
        },
        {
          role: "user",
          content: `Based on the research provided below, create a practical, actionable plan for this bioengineering student.

The student is working on:
${this.input.match(/#+.*Research Topic.*\n\*\*(.+?)\*\*/s)?.[1] || this.input.substring(0, 200) || 'the topic described in the research'}

---

${this.input}

---

Now provide your structured response following the format specified above.`

        }
      ]
    };

    try {
      const res = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json", 
          "Authorization": `Bearer ${this.apiKey}` 
        },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        throw new Error(`OpenAI API request failed: ${res.status} ${res.statusText}`);
      }

      const json = await res.json() as OpenAIResponse;
      const text = json?.choices?.[0]?.message?.content ?? JSON.stringify(json, null, 2);
      
      console.log('✅ OpenAI synthesis completed');
      return text;
    } catch (error) {
      console.error('❌ OpenAI API failed, falling back to simulation:', error);
      return this.generateSimulatedSynthesis();
    }
  }

  private generateSimulatedSynthesis(): string {
    console.log('🔄 Using simulated synthesis...');

    // If course detected, use course-specific synthesis
    if (this.detectedCourse) {
      return this.generateCourseSpecificSynthesis();
    }

    const lower = this.input.toLowerCase();

    // ART CONTEXT
    if (/art style:/i.test(this.input)) {
      const styleMatch = /Art style:\s*([^,]+(?:,\s*[^,]+)*)/i.exec(this.input);
      const style = styleMatch ? styleMatch[1].trim() : 'paper, colored pencils, freehand';
      const promptMatch = /Prompt:\s*([^\n]+)/i.exec(this.input);
      const promptText = promptMatch ? promptMatch[1].trim() : 'abstract drawing with vibrant colors';
      const q = encodeURIComponent(`${style} ${promptText}`);

      return `# Direct Answers
- Use a saturated palette (cerise, turquoise, canary, violet) with one dark anchoring tone.
- Build layers: light base > mid-tones > selective burnish with white for glow.
- Use dynamic, imperfect linework and asymmetry to convey energy.
- Keep 3–4 color families; reserve black sparingly for emphasis.
- Inspiration links: 
  - Google Images: https://www.google.com/search?q=${q}
  - Pinterest: https://www.pinterest.com/search/pins/?q=${q}
  - Behance projects: https://www.behance.net/search/projects?search=${q}
  - Color palettes: https://color.adobe.com/explore
  - Composition ideas: https://www.pinterest.com/search/pins/?q=${encodeURIComponent('abstract composition thumbnails')}

# Next Actions
- Sketch 3 thumbnails (radial, diagonal, grid-breaker) in 5 minutes each.
- Choose 3–4 core colors; create a 2x3 swatch grid and test blends.
- Lightly block shapes; reserve highlights; avoid heavy outlines early.
- Layer mid-tones; deepen contrast; add 5–7 energetic lines to imply motion.
- Burnish selective highlights; add one accent color (≤5% area) for focal pop.
- Compare against references; tweak palette and contrast.

# Materials (if relevant)
- Smooth paper (Bristol or mixed media), colored pencils (incl. white), kneaded eraser, sharpener, ruler.

# Risks & Mitigations
- Overworking paper → Use light pressure; burnish only at end.
- Muddy blends → Keep color families limited; test on scraps first.
- Flat composition → Push contrast; add directional lines and focal accent.

# References
- Google Images query above
- Pinterest board query above
- Behance projects query above`;
    }

    // CIRCUITS / HOMEWORK CONTEXT
    if (lower.includes('circuit') || lower.includes('rms') || lower.includes('homework')) {
      return `# Direct Answers
- RMS: i_rms = sqrt((1/T) ∫_0^T i^2(t) dt). Average (rectified): i_avg = (1/T) ∫_0^T |i(t)| dt.
- Form factor = i_rms / i_avg.
- For ramp i(t)=k t over 0..T0: ∫ i^2 dt = k^2 T0^3 / 3; ∫ |i| dt = k T0^2 / 2.
- For pulses: integrate per interval, sum contributions, then normalize by T.
- Check units and use one full period T.

# Next Actions
- Identify one full period T and write piecewise i(t) over [0, T].
- Compute ∫ i^2(t) dt per interval; sum → i_rms = sqrt((1/T) total).
- Compute ∫ |i(t)| dt per interval; sum → i_avg = (1/T) total.
- Compute form factor = i_rms / i_avg; sanity-check extremes and dimensions.
- Optionally verify numerically with a small script (Python/MATLAB).

# Materials (if relevant)
- Paper, calculator or CAS, or Python/MATLAB.

# Risks & Mitigations
- Wrong period → Sketch waveform and mark T.
- Missing absolute for average → Use |i(t)|.
- Algebra slips → Keep symbols until final; then plug numbers.

# References
- RMS: https://en.wikipedia.org/wiki/Root_mean_square
- Average/rectified values: https://www.allaboutcircuits.com/textbook/alternating-current/chpt-2/rms-rectified-average-values/
- Piecewise integration refresher: https://www.khanacademy.org/math/calculus-1/integration-calc1`;
    }

    // GENERIC FALLBACK
    return `# Direct Answers
- Define the MVP for "${(this.input.match(/\*\*(.+)\*\*/)?.[1] || 'your project')}" (what it must do in week 1).
- Pick and lock the stack (TypeScript scripts + GitHub Actions already in this repo).
- Use existing workflows as automation (research/synthesis, art, homework, project).
- Track work in PRs; each feature = branch + PR with a short checklist.
- Ship something end-to-end today (one workflow from input → PR).

# Next Actions
- Create issues: "MVP scope", "First user prompt flow", "Error handling & logging".
- Wire environment: set OPENAI_API_KEY and PPLX_API_KEY locally and in repo Secrets.
- Run locally: "npm run research" then "npm run synthesize"; review outputs.
- Trigger CI: run Personal Project Help with a concrete topic; review PR.
- Add guardrails: update prompts to enforce concise Direct Answers and Next Actions.
- Add test: minimal unit test for "scripts/*.ts" happy-path.

# Materials (if relevant)
- Node 20, npm, your API keys, GitHub PAT with repo write.

# Risks & Mitigations (optional)
- Vague prompts → Add input templates in docs/briefs; assert required fields.
- CI push failures → Ensure ACTIONS_PAT repo Secret with repo:write + SSO enabled.
- Noisy outputs → Tighten prompts; add post-process filters for sections.

# References (optional)
- Repo root: https://github.com/jonnyterrero/JonnyJr
- Actions (workflows): .github/workflows/
  - art-inspiration.yml, homework-help.yml, project-assistant.yml
- Scripts: scripts/research.ts, scripts/synthesize.ts
- Secrets setup: Settings → Secrets and variables → Actions`;
  }

  private generateCourseSpecificSynthesis(): string {
    if (!this.detectedCourse) return '';
    
    const course = this.detectedCourse;
    const subject = course.subject;
    
    let synthesis = `# Direct Answers\n`;
    
    if (subject === 'Bioengineering') {
      synthesis += `- Review key concepts from ${course.name}: ${course.commonTopics.slice(0, 3).join(', ')}\n`;
      synthesis += `- Apply engineering principles while considering biological constraints\n`;
      synthesis += `- Use ${course.tools[0] || 'MATLAB/Python'} for analysis and verification\n`;
      synthesis += `- Reference: ${course.textbooks[0] || 'course textbook'} for theoretical background\n`;
      synthesis += `- Consider regulatory and safety implications if applicable\n\n`;
    } else if (subject === 'Mathematics') {
      synthesis += `- Identify the type of problem (ODE, PDE, transform, etc.)\n`;
      synthesis += `- Show all steps clearly with proper notation\n`;
      synthesis += `- Verify solution using ${course.tools[0] || 'MATLAB/Python'} or symbolic computation\n`;
      synthesis += `- Check boundary conditions and initial values\n`;
      synthesis += `- Reference: ${course.textbooks[0] || 'course textbook'} for formulas and methods\n\n`;
    } else if (subject === 'Physics') {
      synthesis += `- Draw clear diagrams showing forces, fields, or circuit elements\n`;
      synthesis += `- Apply fundamental principles (conservation laws, field equations, etc.)\n`;
      synthesis += `- Show all work with proper units and significant figures\n`;
      synthesis += `- Verify numerically using ${course.tools[0] || 'appropriate tools'}\n`;
      synthesis += `- Reference: ${course.textbooks[0] || 'course textbook'} for constants and formulas\n\n`;
    } else {
      synthesis += `- Understand core concepts in ${course.name}\n`;
      synthesis += `- Use ${course.tools.join(' or ')} as appropriate\n`;
      synthesis += `- Reference: ${course.textbooks[0] || 'course textbook'}\n`;
      synthesis += `- Show all work and reasoning clearly\n\n`;
    }
    
    synthesis += `# Next Actions\n`;
    synthesis += `- [ ] Review course notes and textbook for relevant concepts\n`;
    synthesis += `- [ ] Identify which ${course.commonTopics[0] || 'topic'} applies to this problem\n`;
    synthesis += `- [ ] Plan solution approach step-by-step\n`;
    synthesis += `- [ ] Work through calculations, showing all steps\n`;
    synthesis += `- [ ] Verify solution using ${course.tools[0] || 'appropriate method'}\n`;
    synthesis += `- [ ] Check for common errors and unit consistency\n`;
    synthesis += `- [ ] Format solution according to assignment requirements\n\n`;
    
    synthesis += `# Materials (if relevant)\n`;
    synthesis += `- ${course.tools.join(', ')}\n`;
    synthesis += `- ${course.textbooks[0] || 'Course textbook'}\n`;
    synthesis += `- Calculator or computational software\n\n`;
    
    synthesis += `# Risks & Mitigations\n`;
    if (subject === 'Mathematics') {
      synthesis += `- Common mistake: Forgetting initial/boundary conditions → Always check them first\n`;
      synthesis += `- Common mistake: Sign errors in algebra → Work slowly and verify each step\n`;
      synthesis += `- Verification: Use symbolic math tools to check final answer\n`;
    } else if (subject === 'Physics') {
      synthesis += `- Common mistake: Unit inconsistencies → Check units at each step\n`;
      synthesis += `- Common mistake: Missing forces in diagrams → Draw complete free body diagram\n`;
      synthesis += `- Verification: Use dimensional analysis and limit checks\n`;
    } else {
      synthesis += `- Review solution for completeness and accuracy\n`;
      synthesis += `- Verify assumptions and approximations\n`;
      synthesis += `- Check against expected physical/biological behavior\n`;
    }
    
    synthesis += `\n# References\n`;
    course.textbooks.slice(0, 3).forEach(book => {
      synthesis += `- ${book}\n`;
    });
    synthesis += `- Course notes and lecture materials\n`;
    synthesis += `- ${course.name} syllabus and assignment guidelines\n`;
    
    // Add relevant resources
    if (this.relevantResources.length > 0) {
      synthesis += `\n## Learning Resources\n`;
      this.relevantResources.slice(0, 8).forEach(resource => {
        synthesis += `- **[${resource.title}](${resource.url})**: ${resource.description}\n`;
      });
    }
    
    return synthesis;
  }

  async saveSynthesis(output: string): Promise<void> {
    const outputFile = 'SYNTHESIS.md';
    fs.writeFileSync(outputFile, output);
    console.log(`📄 Synthesis report saved to ${outputFile}`);
  }
}

// Main execution
async function main() {
  try {
    const inputFile = process.argv[2] || "RESEARCH.md";
    console.log(`🚀 Starting synthesis for input: "${inputFile}"`);
    
    const synthesizer = new ResearchSynthesizer(inputFile);
    await synthesizer.loadInput();
    
    const synthesisResult = await synthesizer.synthesizeWithOpenAI();
    
    // Write to stdout for piping, or save to file
    if (process.argv.includes('>')) {
      process.stdout.write(synthesisResult);
    } else {
      await synthesizer.saveSynthesis(synthesisResult);
    }
    
    console.log('🎉 Synthesis workflow completed successfully!');
  } catch (error) {
    console.error('❌ Synthesis failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { ResearchSynthesizer };
