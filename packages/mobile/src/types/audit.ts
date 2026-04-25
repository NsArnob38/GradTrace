export type AuditSummary = {
  id: string;
  transcriptId: string;
  program: string;
  eligible: boolean;
  cgpa: number;
  creditsEarned: number;
  totalRequired: number;
  issuesCount: number;
  createdAt?: string;
};

export type CourseRecord = {
  course_code: string;
  credits: number;
  grade: string;
};

export type TranscriptCourseRow = {
  course_code: string;
  course_name?: string;
  credits: number;
  grade: string;
  semester?: string;
};

export type AuditDetail = {
  meta?: {
    program?: string;
    concentration?: string;
  };
  level_1?: {
    credits_earned?: number;
    credits_attempted?: number;
  };
  level_2?: {
    cgpa?: number;
    standing?: string;
    quality_points?: number;
    gpa_credits?: number;
  };
  level_3?: {
    eligible?: boolean;
    total_credits_required?: number;
    reasons?: string[];
    remaining?: Record<string, Record<string, number>>;
    prereq_violations?: Array<{ course: string; semester: string; missing: string[] }>;
  };
  roadmap?: {
    estimated_semesters?: number;
    steps?: Array<{ action?: string; detail?: string; category?: string; priority?: string }>;
  };
  courses?: CourseRecord[];
};

export type UploadFileAsset = {
  uri: string;
  name: string;
  mimeType: string;
  sizeBytes: number;
};
