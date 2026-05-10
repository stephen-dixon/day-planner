export type TaskStatus = 'active' | 'todo' | 'done' | 'archived' | string;
export type EnergyLevel = 'low' | 'medium' | 'high' | 'unknown';
export type FocusRequired = 'shallow' | 'medium' | 'deep' | 'unknown';
export type FocusState = 'scattered' | 'okay' | 'deep' | 'unknown';
export type TaskContext = 'coding' | 'writing' | 'admin' | 'household' | 'errands' | 'social' | 'research' | 'planning' | 'other' | 'unknown';
export type TaskPhase = 'vague' | 'clarifying' | 'decomposing' | 'executable' | 'executing' | 'refining' | 'blocked' | 'done';
export type MomentumState = 'stalled' | 'warming_up' | 'engaged' | 'flowing' | 'finishing' | 'unknown';
export type DayBlockStatus = 'planned' | 'done' | 'skipped';
export type DayBlockType = 'task' | 'step' | 'goal' | 'break' | 'buffer' | 'admin' | 'calendar' | 'other';
export type CommitmentStrength = 'hard' | 'soft' | 'optional';

export type Tag = {
  id: number;
  name: string;
  color: string;
};

export type TagCreate = {
  name: string;
  color: string;
};

export type Project = {
  id: number;
  name: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type ProjectCreate = {
  name: string;
  notes?: string | null;
};

export type Milestone = {
  id: number;
  project_id: number;
  name: string;
  due_date: string | null;
  created_at: string;
  updated_at: string;
};

export type MilestoneCreate = {
  project_id: number;
  name: string;
  due_date?: string | null;
};

export type Task = {
  id: number;
  title: string;
  notes: string | null;
  status: TaskStatus;
  priority: number;
  estimated_minutes: number | null;
  deadline: string | null;
  due_date: string | null;
  planned_date: string | null;
  tags: Tag[];
  tag_ids: number[];
  project_id: number | null;
  milestone_id: number | null;
  is_recurring: boolean;
  recurrence_type: string | null;
  recurrence_interval_days: number | null;
  recurrence_weekdays: number[];
  recurrence_min_days: number | null;
  recurrence_max_days: number | null;
  is_habit: boolean;
  source_type: 'local' | 'todoist' | 'github' | 'jira' | 'external';
  source_id: string | null;
  source_url: string | null;
  source_label: string | null;
  energy_required: EnergyLevel;
  activation_cost: EnergyLevel;
  focus_required: FocusRequired;
  interest_level: EnergyLevel;
  context: TaskContext;
  task_phase: TaskPhase;
  clarity_progress: number | null;
  momentum_state: MomentumState;
  starter_step: string | null;
  friction_notes: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskCreate = {
  title: string;
  notes?: string | null;
  status?: TaskStatus;
  priority?: number;
  estimated_minutes?: number | null;
  deadline?: string | null;
  due_date?: string | null;
  planned_date?: string | null;
  tag_ids?: number[];
  project_id?: number | null;
  milestone_id?: number | null;
  is_recurring?: boolean;
  recurrence_type?: string | null;
  recurrence_interval_days?: number | null;
  recurrence_weekdays?: number[];
  recurrence_min_days?: number | null;
  recurrence_max_days?: number | null;
  is_habit?: boolean;
  source_type?: 'local' | 'todoist' | 'github' | 'jira' | 'external';
  source_id?: string | null;
  source_url?: string | null;
  source_label?: string | null;
  energy_required?: EnergyLevel;
  activation_cost?: EnergyLevel;
  focus_required?: FocusRequired;
  interest_level?: EnergyLevel;
  context?: TaskContext;
  task_phase?: TaskPhase;
  clarity_progress?: number | null;
  momentum_state?: MomentumState;
  starter_step?: string | null;
  friction_notes?: string | null;
};

export type TaskUpdate = Partial<TaskCreate>;

export type DayBlock = {
  id: number;
  task_id: number | null;
  task_step_id: number | null;
  date: string;
  start_minute: number;
  end_minute: number;
  block_type: DayBlockType;
  title_override: string | null;
  status: DayBlockStatus;
  commitment_strength: CommitmentStrength;
  created_at: string;
  updated_at: string;
};

export type DayBlockCreate = {
  task_id?: number | null;
  task_step_id?: number | null;
  start_minute: number;
  end_minute: number;
  block_type?: DayBlockType;
  title_override?: string | null;
  status?: DayBlockStatus;
  commitment_strength?: CommitmentStrength;
};

export type DayBlockUpdate = Partial<DayBlockCreate>;

export type TaskStep = {
  id: number;
  task_id: number;
  title: string;
  notes: string | null;
  status: 'todo' | 'done' | 'skipped';
  order_index: number;
  estimated_minutes: number | null;
  activation_cost: EnergyLevel;
  can_do_low_energy: boolean;
  created_at: string;
  updated_at: string;
};

export type TaskStepCreate = {
  title: string;
  notes?: string | null;
  status?: 'todo' | 'done' | 'skipped';
  order_index?: number | null;
  estimated_minutes?: number | null;
  activation_cost?: EnergyLevel;
  can_do_low_energy?: boolean;
};

export type TaskStepUpdate = Partial<TaskStepCreate>;

export type TaskRecommendation = {
  task: Task;
  score: number;
  reasons: string[];
};

export type SupportRecommendRequest = {
  energy: EnergyLevel;
  focus: FocusState;
  mood?: string | null;
  available_minutes?: number | null;
  preferred_context?: TaskContext | null;
};

export type TaskEnrichment = {
  suggested_energy_required: EnergyLevel;
  suggested_activation_cost: EnergyLevel;
  suggested_focus_required: FocusRequired;
  suggested_interest_level: EnergyLevel;
  suggested_context: TaskContext;
  suggested_task_phase: TaskPhase;
  suggested_starter_step: string | null;
  reasoning: string | null;
};

export type TaskBreakdown = {
  starter_step: string;
  suggested_steps: string[];
  suggested_block_minutes: number | null;
  reasoning: string | null;
};

export type SessionReflection = {
  inferred_friction_reason: string | null;
  suggested_task_phase: TaskPhase;
  suggested_next_action: string;
  reasoning: string | null;
};

export type SuggestedBlock = {
  task_id: number | null;
  task_step_id: number | null;
  title: string;
  start_minute: number;
  end_minute: number;
  reasoning: string;
};

export type PlannedDayProposal = {
  summary: string;
  warnings: string[];
  suggested_blocks: SuggestedBlock[];
  rationale: string;
};

export type AIStatus = {
  configured: boolean;
  provider: string;
  model: string;
  base_url: string | null;
  message: string | null;
};

export type TaskAnalytics = {
  task_id: number;
  average_actual_minutes: number | null;
  estimate_ratio: number | null;
  average_sessions_to_completion: number | null;
  reschedule_count: number;
  abandonment_rate: number | null;
  confidence_level: string;
  duration_summary: string;
  activation_risk: string;
  common_friction_reasons: string[];
  timing_patterns: string[];
  signals_used: string[];
};

export type ContextAnalytics = {
  context: string;
  task_count: number;
  completed_session_count: number;
  average_actual_minutes: number | null;
  abandonment_rate: number | null;
  common_friction_reasons: string[];
  summary: string;
  signals_used: string[];
};

export type ExternalCalendarStatus = {
  provider: 'google' | 'microsoft' | string;
  connected: boolean;
  account_email: string | null;
  scope: string | null;
  expires_at: string | null;
};

export type ExternalCalendarBlock = {
  id: number;
  provider: 'google' | 'microsoft' | string;
  date: string;
  start_minute: number;
  end_minute: number;
  title: string | null;
  busy_status: string;
};

export type GitHubConfig = {
  default_owner: string | null;
  default_repo: string | null;
  configured: boolean;
};

export type GitHubMilestone = {
  number: number;
  title: string;
  description: string | null;
  state: string;
  open_issues: number;
  closed_issues: number;
  due_on: string | null;
};

export type GitHubIssue = {
  external_work_item_id: number | null;
  external_id: string;
  number: number;
  title: string;
  body: string | null;
  url: string;
  state: string;
  labels: string[];
  milestone_title: string | null;
  imported_task_id: number | null;
  ignored: boolean;
};

export type ImportGitHubIssueRequest = {
  owner: string;
  repo: string;
  issue_number: number;
  estimated_minutes?: number | null;
  priority?: number | null;
};

export type TaskCatalog = {
  name: string;
  locked: boolean;
  db_path: string;
};

export type CatalogSession = {
  name: string;
  token: string;
};

export type TaskCompletion = {
  id: number;
  task_id: number;
  completed_on: string;
  source_block_id: number | null;
  created_at: string;
};

export type HabitStats = {
  task: Task;
  timeframe_days: number;
  completions: TaskCompletion[];
  completion_count: number;
  expected_min: number;
  expected_max: number;
  status: string;
  average_gap_days: number | null;
};
