#!/usr/bin/env node

import { writeFileSync, readFileSync, existsSync } from 'fs';
import { execSync } from 'child_process';
import { join } from 'path';
import fetch from "node-fetch";

interface ResearchTopic {
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed';
}

interface ResearchFindings {
  date: string;
  topics: ResearchTopic[];
  insights: string[];
  nextSteps: string[];
  perplexityResults: string;
  category: string;
}

interface CategoryMapping {
  keywords: string[];
  category: string;
}

interface PerplexityResponse {
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

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  try {
    return JSON.stringify(error);
  } catch {
    return String(error);
  }
}

class AIResearch {
  private findings: ResearchFindings;
  private topic: string;
  private apiKey: string;
  private categoryMappings: CategoryMapping[];
  private coursesConfig: CoursesConfig | null = null;
  private detectedCourse: CourseInfo | null = null;
  private resourcesConfig: ResourcesConfig | null = null;
  private relevantResources: Resource[] = [];

  constructor(topic: string = "repo roadmap") {
    this.topic = topic;
    this.apiKey = process.env.PPLX_API_KEY || '';
    this.loadCoursesConfig();
    this.loadResourcesConfig();
    this.detectCourse();
    this.loadRelevantResources();
    
    this.categoryMappings = [
      {
        keywords: ['project', 'build', 'create', 'develop', 'app', 'website', 'software', 'tool'],
        category: 'Personal Projects'
      },
      {
        keywords: ['think', 'reflect', 'philosophy', 'meaning', 'purpose', 'life', 'personal', 'growth'],
        category: 'Reflections & Questions'
      },
      {
        keywords: ['math', 'mathematics', 'algorithm', 'code', 'programming', 'function', 'equation', 'calculate'],
        category: 'Math & Coding'
      },
      {
        keywords: ['science', 'physics', 'chemistry', 'biology', 'research', 'experiment', 'theory', 'hypothesis'],
        category: 'Sciences'
      }
    ];
    
    // Add course-specific keywords to category mappings
    if (this.coursesConfig) {
      for (const [code, course] of Object.entries(this.coursesConfig.courses)) {
        const existingMapping = this.categoryMappings.find(m => m.category === course.category);
        if (existingMapping) {
          existingMapping.keywords.push(...course.keywords.map(k => k.toLowerCase()));
        }
      }
    }
    
    this.findings = {
      date: new Date().toISOString().split('T')[0],
      topics: [],
      insights: [],
      nextSteps: [],
      perplexityResults: '',
      category: this.categorizeTopic(topic)
    };
  }

  private loadCoursesConfig(): void {
    try {
      // Try multiple paths to find courses.json
      const possiblePaths = [
        join(process.cwd(), 'scripts', 'courses.json'),
        join(__dirname, 'courses.json'),
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
        console.log(`📚 Loaded course configuration (${Object.keys(this.coursesConfig.courses).length} courses)`);
      } else {
        console.log('⚠️  courses.json not found, using default mappings');
      }
    } catch (error) {
      console.warn('⚠️  Failed to load courses.json:', getErrorMessage(error));
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
        console.log('📚 Loaded resources configuration');
      }
    } catch (error) {
      console.warn('⚠️  Failed to load resources.json:', getErrorMessage(error));
    }
  }

  private detectCourse(): void {
    if (!this.coursesConfig) return;
    
    const topicUpper = this.topic.toUpperCase();
    
    // Try to match course codes (e.g., MAP2302, BME3100C, PHY2049)
    for (const [code, courseInfo] of Object.entries(this.coursesConfig.courses)) {
      if (topicUpper.includes(code) || topicUpper.includes(code.replace(/\d+/g, ''))) {
        this.detectedCourse = courseInfo;
        console.log(`🎓 Detected course: ${code} - ${courseInfo.name}`);
        break;
      }
    }
    
    // If no direct match, try keyword matching
    if (!this.detectedCourse) {
      const topicLower = this.topic.toLowerCase();
      for (const [code, courseInfo] of Object.entries(this.coursesConfig.courses)) {
        const matchedKeywords = courseInfo.keywords.filter(kw => 
          topicLower.includes(kw.toLowerCase())
        );
        if (matchedKeywords.length >= 2) {
          this.detectedCourse = courseInfo;
          console.log(`🎓 Detected course by keywords: ${code} - ${courseInfo.name}`);
          break;
        }
      }
    }
    
    if (this.detectedCourse) {
      this.findings.category = this.detectedCourse.category;
    }
  }

  private loadRelevantResources(): void {
    if (!this.resourcesConfig) return;
    
    const resources: Resource[] = [];
    const topicLower = this.topic.toLowerCase();
    
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
      { keywords: ['python'], paths: ['programming.python'] },
      { keywords: ['art', 'drawing', 'paint'], paths: ['art.inspiration'] }
    ];
    
    for (const { keywords, paths } of topicKeywords) {
      if (keywords.some(kw => topicLower.includes(kw))) {
        for (const path of paths) {
          const [category, subcategory] = path.split('.');
          const categoryResources = this.resourcesConfig.resources[category];
          if (categoryResources && categoryResources[subcategory]) {
            resources.push(...categoryResources[subcategory]);
          }
        }
      }
    }
    
    // Add general tools and reference
    if (this.resourcesConfig.resources.tools) {
      resources.push(...(this.resourcesConfig.resources.tools.calculators || []).slice(0, 2));
      resources.push(...(this.resourcesConfig.resources.tools.reference || []).slice(0, 2));
    }
    
    // Remove duplicates based on URL
    const seenUrls = new Set<string>();
    this.relevantResources = resources.filter(resource => {
      if (seenUrls.has(resource.url)) return false;
      seenUrls.add(resource.url);
      return true;
    });
    
    if (this.relevantResources.length > 0) {
      console.log(`🔗 Loaded ${this.relevantResources.length} relevant resources`);
    }
  }

  private categorizeTopic(topic: string): string {
    const lowerTopic = topic.toLowerCase();
    
    for (const mapping of this.categoryMappings) {
      if (mapping.keywords.some(keyword => lowerTopic.includes(keyword))) {
        return mapping.category;
      }
    }
    
    return 'General Research';
  }

  async conductResearch(): Promise<void> {
    console.log('🔬 Starting AI research...');
    console.log(`📝 Research topic: ${this.topic}`);
    console.log(`📂 Category: ${this.findings.category}`);
    console.log(`🔑 API Key present: ${this.apiKey ? 'Yes ✅' : 'No ❌'}`);
    
    if (this.detectedCourse) {
      console.log(`🎓 Course detected: ${this.detectedCourse.name}`);
    }
    
    if (this.relevantResources.length > 0) {
      console.log(`📚 Loaded ${this.relevantResources.length} relevant resources`);
    }
    
    if (!this.apiKey) {
      console.warn('⚠️  PPLX_API_KEY not found. Using simulated research data.');
      console.warn('💡 To use real Perplexity research, set PPLX_API_KEY environment variable.');
      console.log('🔄 Generating simulated research...');
      await this.simulateResearch();
      return;
    }

    console.log('🚀 Attempting real Perplexity API research...');
    console.log('⏳ This may take 30-60 seconds...');
    
    try {
      await this.perplexityResearch();
      console.log('✅ Research completed successfully');
    } catch (error) {
      console.error('❌ Perplexity API failed, falling back to simulation');
      console.error('🔍 Error details:', getErrorMessage(error));
      console.log('🔄 Generating fallback research...');
      await this.simulateResearch();
    }
  }

  async perplexityResearch(): Promise<void> {
    console.log('🤖 Querying Perplexity API...');
    console.log(`🔑 Using API key: ${this.apiKey.substring(0, 8)}...`);
    
    // Build user context
    const userContext = `You are a research assistant helping a dedicated bioengineering student who:
- Major: Bioengineering (focus on medical devices, biomaterials, tissue engineering)
- Minors: Chemistry and Computer Science
- Learning Style: Self-directed, project-oriented, religiously self-studies alongside coursework
- Active Projects: Multiple personal projects (see GitHub workspace)
- Current Focus: Summer 2025 - MAP2302 (Differential Equations) and PHY2049 (Physics II)
- Upcoming: Fall 2025 - Multiple BME courses including Biomaterials, Physiology, Circuits, Healthcare Engineering`;

    let researchPrompt = `${userContext}\n\nPlease provide a comprehensive, practical research brief on the following topic:

**Research Topic:** ${this.topic}

**Your Task:** Provide actionable research that helps this student understand, solve problems, and complete assignments effectively.`;

    // Add course-specific context if detected
    if (this.detectedCourse) {
      researchPrompt += `\n\n**Course Context:**
- Course: ${this.detectedCourse.name} (${this.detectedCourse.subject})
- Credits: ${this.detectedCourse.credits}
- Term: ${this.detectedCourse.term}
- Status: ${this.detectedCourse.current ? 'Currently Enrolled' : this.detectedCourse.upcoming ? 'Upcoming' : 'Past Course'}
- Common Topics Covered: ${this.detectedCourse.commonTopics.join(', ')}
- Recommended Textbooks: ${this.detectedCourse.textbooks.join(', ')}
- Tools Used: ${this.detectedCourse.tools.join(', ')}
- Typical Assignments: ${this.detectedCourse.typicalAssignments.join(', ')}`;
    }

    // Add relevant resources
    if (this.relevantResources.length > 0) {
      researchPrompt += `\n\n**Relevant Learning Resources Available:**
${this.relevantResources.slice(0, 10).map(r => `- **${r.title}**: ${r.url}\n  ${r.description}`).join('\n')}

You may reference these resources in your response.`;
    }

    researchPrompt += `\n\n**Required Response Format:**

Please structure your response with these sections:

1. **Executive Summary** (2-3 sentences)
   - Quick overview of what this topic involves
   - Why it's relevant to a bioengineering student

2. **Key Concepts & Theory** (5-7 bullet points)
   - Fundamental principles and definitions
   - Core equations, formulas, or concepts
   - Relationships between concepts
   - Focus on practical understanding, not just theory

3. **Step-by-Step Problem-Solving Approach**
   - Methodical approach to solving problems in this area
   - Break down complex problems into manageable steps
   - Include example problem-solving strategies

4. **Common Mistakes & How to Avoid Them**
   - Typical errors students make
   - How to recognize and prevent them
   - Verification strategies

5. **Practical Applications & Examples**
   - Real-world applications in bioengineering/medicine
   - Connection to other courses (chemistry, CS, physics)
   - If applicable: connection to medical devices or healthcare

6. **Recommended Resources & Next Steps**
   - Best textbooks or sources for deeper learning
   - Practice problems or exercises
   - Study strategies specific to this topic
   - Related topics to explore next

7. **Quick Reference** (if applicable)
   - Key formulas in one place
   - Important constants or values
   - Cheat sheet style summary

**Guidelines:**
- Be concise but comprehensive
- Use clear, accessible language
- Include concrete examples where possible
- Focus on practical application, not just theory
- Connect concepts to bioengineering when relevant
- Provide actionable steps the student can follow immediately`;

    const body = {
      model: "pplx-7b-chat",
      messages: [{ role: "user", content: researchPrompt }],
      search_domain_filter: ["web"],
    };

    console.log('📤 Sending request to Perplexity API...');
    const res = await fetch("https://api.perplexity.ai/chat/completions", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json", 
        "Authorization": `Bearer ${this.apiKey}` 
      },
      body: JSON.stringify(body)
    });

    console.log(`📥 API Response Status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error('❌ API Error Response:', errorText);
      throw new Error(`API request failed: ${res.status} ${res.statusText} - ${errorText}`);
    }

    const json = await res.json() as PerplexityResponse;
    console.log('📋 API Response received, processing...');
    
    const text = json?.choices?.[0]?.message?.content ?? "No result";
    console.log(`📝 Response length: ${text.length} characters`);
    
    if (text === "No result" || text.trim().length < 50) {
      console.error('❌ Insufficient response from API');
      throw new Error("Perplexity API returned insufficient results");
    }
    
    this.findings.perplexityResults = text;
    console.log('✅ Perplexity research completed successfully');
    
    // Process the results into structured data
    this.processPerplexityResults(text);
  }

  private processPerplexityResults(text: string): void {
    // Extract insights from Perplexity response
    const lines = text.split('\n').filter(line => line.trim());
    
    // Create research topics based on the response
    this.findings.topics = [
      {
        title: this.topic,
        description: `Research findings from Perplexity AI for: ${this.topic}`,
        priority: 'high' as const,
        status: 'completed' as const
      }
    ];

    // Extract key insights with better parsing
    const insights = [];
    let inInsightsSection = false;
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Look for section headers
      if (trimmedLine.toLowerCase().includes('key findings') || 
          trimmedLine.toLowerCase().includes('insights') ||
          trimmedLine.toLowerCase().includes('findings')) {
        inInsightsSection = true;
        continue;
      }
      
      // Stop at next major section
      if (inInsightsSection && (trimmedLine.toLowerCase().includes('sources') ||
          trimmedLine.toLowerCase().includes('references') ||
          trimmedLine.toLowerCase().includes('next steps') ||
          trimmedLine.toLowerCase().includes('applications'))) {
        break;
      }
      
      // Extract bullet points and numbered items
      if (inInsightsSection && (trimmedLine.startsWith('•') || 
          trimmedLine.startsWith('-') || 
          trimmedLine.startsWith('*') ||
          trimmedLine.match(/^\d+\./))) {
        const insight = trimmedLine.replace(/^[•\-\*\d+\.]\s*/, '').trim();
        if (insight.length > 10) { // Only include substantial insights
          insights.push(insight);
        }
      }
    }
    
    // Fallback to simple bullet point extraction if section parsing failed
    if (insights.length === 0) {
      this.findings.insights = lines
        .filter(line => line.includes('•') || line.includes('-') || line.includes('*'))
        .slice(0, 5)
        .map(line => line.replace(/^[•\-\*]\s*/, '').trim())
        .filter(insight => insight.length > 10);
    } else {
      this.findings.insights = insights.slice(0, 5);
    }

    // Generate next steps based on the research
    this.findings.nextSteps = [
      'Review and validate research findings',
      'Implement recommendations from the research',
      'Schedule follow-up research if needed',
      'Document key insights for future reference'
    ];
  }

  async simulateResearch(): Promise<void> {
    console.log('🔄 Using simulated research data...');
    
    // Create meaningful research topics based on the input
    const topicLower = this.topic.toLowerCase();
    
    // If we detected a course, use course-specific knowledge
    if (this.detectedCourse) {
      this.generateCourseSpecificResearch();
      return;
    }
    
    // Generate relevant research topics based on keywords
    const researchTopics: ResearchTopic[] = [];
    
    if (topicLower.includes('biomaterial') || topicLower.includes('material')) {
      researchTopics.push(
        {
          title: 'Biomaterials for Medical Applications',
          description: 'Research into biocompatible materials for implants and medical devices',
          priority: 'high' as const,
          status: 'in_progress' as const
        },
        {
          title: 'Tissue Engineering Materials',
          description: 'Advanced materials for regenerative medicine and tissue scaffolds',
          priority: 'high' as const,
          status: 'pending' as const
        },
        {
          title: 'PRISMA Protocol Development',
          description: 'Systematic review methodology for biomaterials research',
          priority: 'medium' as const,
          status: 'pending' as const
        }
      );
    } else if (topicLower.includes('math') || topicLower.includes('laplace') || topicLower.includes('equation') || topicLower.includes('circuit') || topicLower.includes('rms')) {
      researchTopics.push(
        {
          title: 'Mathematical Analysis Techniques',
          description: 'Advanced methods for solving differential equations and transforms',
          priority: 'high' as const,
          status: 'in_progress' as const
        },
        {
          title: 'Circuit Signals and RMS/Average',
          description: 'Formulas and procedures for RMS, average, and form factor',
          priority: 'high' as const,
          status: 'pending' as const
        }
      );
    } else if (topicLower.includes('project') || topicLower.includes('build') || topicLower.includes('develop')) {
      researchTopics.push(
        {
          title: 'Project Planning and Management',
          description: 'Best practices for project development and execution',
          priority: 'high' as const,
          status: 'in_progress' as const
        },
        {
          title: 'Technology Stack Selection',
          description: 'Choosing appropriate tools and frameworks for development',
          priority: 'medium' as const,
          status: 'pending' as const
        }
      );
    } else {
      // Default research topics
      researchTopics.push(
        {
          title: this.topic,
          description: `Research analysis for: ${this.topic}`,
          priority: 'high' as const,
          status: 'in_progress' as const
        },
        {
          title: 'Related Research Areas',
          description: 'Exploring connected topics and methodologies',
          priority: 'medium' as const,
          status: 'pending' as const
        }
      );
    }

    this.findings.topics = researchTopics;

    // Generate contextual insights based on the topic
    let insights = [];
    
    if (topicLower.includes('biomaterial')) {
      insights = [
        'Recent advances in biocompatible materials show promise for medical applications',
        'PRISMA guidelines provide systematic framework for evidence synthesis',
        'Tissue engineering requires careful material selection and biocompatibility testing',
        'Systematic reviews help identify gaps in current research',
        'Material properties must balance mechanical strength with biological compatibility'
      ];
    } else if (topicLower.includes('math') || topicLower.includes('laplace')) {
      insights = [
        'Laplace transforms provide powerful tools for solving differential equations',
        'Numerical methods offer computational alternatives to analytical solutions',
        'MATLAB and Python provide robust platforms for mathematical computation',
        'Understanding mathematical foundations is crucial for engineering applications',
        'Systematic approaches help organize complex mathematical problems'
      ];
    } else if (topicLower.includes('circuit') || topicLower.includes('rms')) {
      insights = [
        'RMS: i_rms = sqrt( (1/T) ∫_0^T i^2(t) dt ); Average (rectified): i_avg = (1/T) ∫_0^T |i(t)| dt',
        'Form factor = i_rms / i_avg; for piecewise signals, compute per interval and sum',
        'For linear ramps i(t)=k t over 0..T0: ∫ i^2 dt = k^2 T0^3 / 3; ∫ |i| dt = k T0^2 / 2',
        'For pulse trains: scale by duty cycle; RMS squares add over non-overlapping intervals',
        'Check units (A, s) and use consistent T for period'
      ];
    } else if (topicLower.includes('art') || topicLower.includes('drawing') || topicLower.includes('paint') || topicLower.includes('art style:')) {
      // Art-specific simulated insights
      const styleMatch = /art style:\s*([^,]+(?:,\s*[^,]+)*)/i.exec(this.topic);
      const style = styleMatch ? styleMatch[1].trim() : 'paper, colored pencils, freehand';
      const promptText = this.topic.replace(/.*prompt:\s*/i, '').trim();
      const query = encodeURIComponent(`${style} ${promptText}`);
      insights = [
        'Favor a vibrant palette (cerise, turquoise, canary, violet) with high-contrast accents',
        'Layer colored pencils from light to dark; burnish highlights with white pencil',
        'Use asymmetric composition and dynamic linework to convey energy and rhythm',
        'Limit color families to 3–4 for cohesion; reserve black sparingly for emphasis',
        `Reference searches: https://www.google.com/search?q=${query}`,
        `Pinterest board ideas: https://www.pinterest.com/search/pins/?q=${query}`,
        `Behance inspiration: https://www.behance.net/search/projects?search=${query}`
      ];
    } else {
      insights = [
        `Key research focus: ${this.topic}`,
        'Systematic approaches improve research quality and reproducibility',
        'Evidence-based methods provide reliable foundations for decision making',
        'Documentation and methodology are crucial for research success',
        'Collaborative approaches enhance research outcomes'
      ];
    }

    this.findings.insights = insights;

    // Generate relevant next steps
    let nextSteps = [];
    
    if (topicLower.includes('biomaterial')) {
      nextSteps = [
        'Conduct systematic literature review using PRISMA guidelines',
        'Identify key material properties and biocompatibility requirements',
        'Analyze current research gaps and opportunities',
        'Develop research protocol and methodology',
        'Plan experimental validation approaches'
      ];
    } else if (topicLower.includes('math') || topicLower.includes('laplace')) {
      nextSteps = [
        'Review mathematical foundations and theory',
        'Implement computational solutions using appropriate software',
        'Validate results through analytical and numerical methods',
        'Document solution methodology and assumptions',
        'Prepare comprehensive analysis and conclusions'
      ];
    } else if (topicLower.includes('circuit') || topicLower.includes('rms')) {
      nextSteps = [
        'Identify period T and piecewise expressions for i(t) over one full period',
        'Compute ∫ i^2(t) dt per interval (use ramp/pulse formulas) and sum → RMS',
        'Compute ∫ |i(t)| dt per interval and sum → Average (rectified)',
        'Calculate form factor = RMS / Average; verify with dimensional checks',
        'Cross-check with numerical approximation in Python/MATLAB',
        'References: https://en.wikipedia.org/wiki/Root_mean_square',
        'Piecewise integration refresher: https://www.khanacademy.org/math/calculus-1/integration-calc1',
        'Signal examples: https://www.allaboutcircuits.com/textbook/alternating-current/chpt-2/rms-rectified-average-values/'
      ];
    } else if (topicLower.includes('art') || topicLower.includes('drawing') || topicLower.includes('paint') || topicLower.includes('art style:')) {
      const styleMatch2 = /art style:\s*([^,]+(?:,\s*[^,]+)*)/i.exec(this.topic);
      const style2 = styleMatch2 ? styleMatch2[1].trim() : 'paper, colored pencils, freehand';
      const promptText2 = this.topic.replace(/.*prompt:\s*/i, '').trim();
      const q = encodeURIComponent(`${style2} ${promptText2}`);
      nextSteps = [
        'Sketch 3 thumbnails (different compositions: radial, diagonal, grid-breaker)',
        'Choose 3–4 colors; make a 2x3 swatch grid and test blends',
        'Block big shapes lightly; reserve highlights; avoid heavy outlines early',
        'Layer mid-tones, then deepen contrast; add 5–7 high-energy lines for motion',
        'Add one unexpected accent color (<=5% area) to create a focal pop',
        `Open refs: Google Images → https://www.google.com/search?q=${q}`,
        `Scan inspiration: Pinterest → https://www.pinterest.com/search/pins/?q=${q}`,
        `Color harmony tool: https://color.adobe.com/create/color-wheel`
      ];
    } else {
      nextSteps = [
        `Develop comprehensive research plan for ${this.topic}`,
        'Identify key resources and methodologies',
        'Create systematic approach to information gathering',
        'Plan implementation and validation steps',
        'Document findings and recommendations'
      ];
    }

    this.findings.nextSteps = nextSteps;

    console.log('✅ Simulated research completed');
  }

  private generateCourseSpecificResearch(): void {
    if (!this.detectedCourse) return;
    
    const course = this.detectedCourse;
    const topicLower = this.topic.toLowerCase();
    
    // Generate research topics based on course
    this.findings.topics = [
      {
        title: this.topic,
        description: `Homework assignment for ${course.name}`,
        priority: 'high' as const,
        status: 'in_progress' as const
      },
      ...course.commonTopics.slice(0, 2).map(topic => ({
        title: topic,
        description: `Related topic in ${course.name}`,
        priority: 'medium' as const,
        status: 'pending' as const
      }))
    ];

    // Generate course-specific insights
    let insights: string[] = [];
    
    if (course.subject === 'Bioengineering') {
      insights = [
        `Focus on practical applications in ${course.name.toLowerCase()}`,
        `Consider both biological and engineering perspectives`,
        `Review relevant regulations and standards if applicable`,
        `Use ${course.tools.join(' or ')} for analysis and verification`,
        `Consult ${course.textbooks[0] || 'course textbook'} for theoretical background`
      ];
    } else if (course.subject === 'Mathematics') {
      insights = [
        `Show all steps clearly for ${course.name.toLowerCase()}`,
        `Verify solutions using ${course.tools.join(' or ')}`,
        `Pay attention to boundary conditions and initial values`,
        `Check units and dimensional consistency`,
        `Reference: ${course.textbooks[0] || 'course textbook'}`
      ];
    } else if (course.subject === 'Physics') {
      insights = [
        `Apply fundamental principles from ${course.name.toLowerCase()}`,
        `Draw clear diagrams and free body diagrams where applicable`,
        `Check units and use appropriate significant figures`,
        `Use ${course.tools.join(' or ')} for numerical verification`,
        `Consult ${course.textbooks[0] || 'course textbook'} for formulas and constants`
      ];
    } else {
      insights = [
        `Focus on understanding core concepts in ${course.name.toLowerCase()}`,
        `Use ${course.tools.join(' or ')} as appropriate`,
        `Reference: ${course.textbooks[0] || 'course textbook'}`,
        `Show all work and reasoning clearly`,
        `Consider practical applications and real-world examples`
      ];
    }
    
    this.findings.insights = insights;

    // Generate course-specific next steps
    this.findings.nextSteps = [
      `Review ${course.name} course materials and notes`,
      `Identify which ${course.commonTopics[0] || 'topic'} concepts apply`,
      `Plan solution approach using ${course.tools[0] || 'appropriate tools'}`,
      `Work through the problem step-by-step`,
      `Verify solution and check for common errors`,
      `Format solution according to course requirements`
    ];
    
    console.log(`✅ Generated course-specific research for ${course.name}`);
  }

  generateReport(): string {
    const report = `# AI Research Report - ${this.findings.date}

## Research Topic
**${this.topic}**

## Category
**${this.findings.category}**

## Research Topics

${this.findings.topics.map(topic => 
  `### ${topic.title}
- **Priority**: ${topic.priority}
- **Status**: ${topic.status}
- **Description**: ${topic.description}
`).join('\n')}

## Key Insights

${this.findings.insights.map(insight => `- ${insight}`).join('\n')}

## Next Steps

${this.findings.nextSteps.map(step => `- ${step}`).join('\n')}

${this.relevantResources.length > 0 ? `
## Learning Resources

${this.relevantResources.slice(0, 10).map(r => `- **[${r.title}](${r.url})**: ${r.description}`).join('\n')}

` : ''}

${this.findings.perplexityResults ? `
## Perplexity AI Research Results

${this.findings.perplexityResults}
` : ''}

---
*Generated by AI Research System on ${new Date().toISOString()}*
`;

    return report;
  }

  async saveReport(): Promise<void> {
    const report = this.generateReport();
    writeFileSync('RESEARCH.md', report);
    console.log('📄 Research report saved to RESEARCH.md');
  }
}

// Main execution
async function main() {
  try {
    const topic = process.argv.slice(2).join(" ") || "repo roadmap";
    console.log(`🚀 Starting research for topic: "${topic}"`);
    
    const research = new AIResearch(topic);
    await research.conductResearch();
    await research.saveReport();
    console.log('🎉 Research workflow completed successfully!');
  } catch (error) {
    console.error('❌ Research failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { AIResearch };
