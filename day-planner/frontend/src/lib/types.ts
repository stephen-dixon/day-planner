export type TaskStatus = 'todo' | 'done' | string;
export type DayBlockStatus = 'planned' | 'done' | string;

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
};

export type TaskUpdate = Partial<TaskCreate>;

export type DayBlock = {
  id: number;
  task_id: number;
  date: string;
  start_minute: number;
  end_minute: number;
  status: DayBlockStatus;
  created_at: string;
  updated_at: string;
};

export type DayBlockCreate = {
  task_id: number;
  start_minute: number;
  end_minute: number;
  status?: DayBlockStatus;
};

export type DayBlockUpdate = Partial<DayBlockCreate>;

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
