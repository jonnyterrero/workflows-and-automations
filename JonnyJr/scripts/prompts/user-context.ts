/**
 * User context profile for better AI responses
 * This context is injected into prompts to help AI understand the user better
 */

export const USER_PROFILE = {
  student: {
    major: "Bioengineering",
    minors: ["Chemistry", "Computer Science"],
    focus: ["Medical devices", "Biomaterials", "Tissue engineering"],
    learningStyle: "Self-directed, project-oriented, active self-study",
    currentTerm: "Summer 2025",
    currentCourses: ["MAP2302 (Differential Equations)", "PHY2049 (Physics II)"],
    upcomingCourses: [
      "BME3100C (Introduction to Biomaterials)",
      "BME3404C (Human Physiology for Engineers II)",
      "BME3506C (Circuits for Bioengineers)",
      "BME4722 (Health Care Engineering)"
    ],
    activities: [
      "Multiple personal programming projects",
      "Religious self-study",
      "Active GitHub contributor",
      "Project-based learning approach"
    ],
    preferences: {
      communication: "Clear, actionable, step-by-step",
      detail: "Practical over theoretical",
      examples: "Real-world applications preferred",
      format: "Structured, scannable markdown"
    }
  }
};

export const PROMPT_ENHANCEMENTS = {
  research: {
    focus: "Practical understanding and problem-solving",
    tone: "Educational, encouraging, clear",
    structure: "Comprehensive but scannable",
    depth: "Sufficient for assignment completion"
  },
  synthesis: {
    focus: "Actionable steps and clear guidance",
    tone: "Practical, direct, helpful",
    structure: "Step-by-step checklists",
    depth: "Executable instructions"
  }
};

export function getUserContextString(): string {
  return `Bioengineering student (Chemistry & CS minor):
- Active self-learner with multiple projects
- Currently: ${USER_PROFILE.student.currentCourses.join(', ')}
- Upcoming: ${USER_PROFILE.student.upcomingCourses.slice(0, 2).join(', ')}...
- Prefers: ${USER_PROFILE.student.preferences.communication}, ${USER_PROFILE.student.preferences.detail}`;
}

