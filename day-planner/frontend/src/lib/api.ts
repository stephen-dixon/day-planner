import type {
  DayBlock,
  DayBlockCreate,
  DayBlockUpdate,
  AIStatus,
  ContextAnalytics,
  PlannedDayProposal,
  SessionReflection,
  SuggestedBlock,
  TaskAnalytics,
  TaskBreakdown,
  TaskEnrichment,
  ExternalCalendarBlock,
  ExternalCalendarStatus,
  GitHubConfig,
  GitHubIssue,
  GitHubMilestone,
  HabitStats,
  ImportGitHubIssueRequest,
  Milestone,
  MilestoneCreate,
  Project,
  ProjectCreate,
  Tag,
  TagCreate,
  CatalogSession,
  TaskCatalog,
  Task,
  TaskCreate,
  TaskRecommendation,
  TaskStep,
  TaskStepCreate,
  TaskStepUpdate,
  SupportRecommendRequest,
  TaskUpdate
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '/api');
const CATALOG_TOKEN_KEY = 'day-planner-catalog-token';
const CATALOG_NAME_KEY = 'day-planner-catalog-name';

export function getSelectedCatalogName(): string {
  if (typeof localStorage === 'undefined') return 'default';
  return localStorage.getItem(CATALOG_NAME_KEY) ?? 'default';
}

export function setSelectedCatalog(session: CatalogSession): void {
  localStorage.setItem(CATALOG_TOKEN_KEY, session.token);
  localStorage.setItem(CATALOG_NAME_KEY, session.name);
}

export function clearSelectedCatalog(): void {
  localStorage.removeItem(CATALOG_TOKEN_KEY);
  localStorage.removeItem(CATALOG_NAME_KEY);
}

function catalogHeaders(): Record<string, string> {
  if (typeof localStorage === 'undefined') return {};
  const token = localStorage.getItem(CATALOG_TOKEN_KEY);
  return token ? { 'X-Catalog-Token': token } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...catalogHeaders(),
      ...options.headers
    }
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export function getCatalogs(): Promise<TaskCatalog[]> {
  return request<TaskCatalog[]>('/catalogs');
}

export function createCatalog(payload: { name: string; password: string }): Promise<TaskCatalog> {
  return request<TaskCatalog>('/catalogs', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function loadCatalog(payload: { name: string; password: string }): Promise<CatalogSession> {
  return request<CatalogSession>('/catalogs/load', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function getTasks(): Promise<Task[]> {
  return request<Task[]>('/tasks');
}

export function getTask(id: number): Promise<Task> {
  return request<Task>(`/tasks/${id}`);
}

export function createTask(payload: TaskCreate): Promise<Task> {
  return request<Task>('/tasks', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function updateTask(id: number, payload: TaskUpdate): Promise<Task> {
  return request<Task>(`/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  });
}

export function deleteTask(id: number): Promise<void> {
  return request<void>(`/tasks/${id}`, {
    method: 'DELETE'
  });
}

export function getTaskSteps(taskId: number): Promise<TaskStep[]> {
  return request<TaskStep[]>(`/tasks/${taskId}/steps`);
}

export function createTaskStep(taskId: number, payload: TaskStepCreate): Promise<TaskStep> {
  return request<TaskStep>(`/tasks/${taskId}/steps`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function updateTaskStep(id: number, payload: TaskStepUpdate): Promise<TaskStep> {
  return request<TaskStep>(`/steps/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  });
}

export function deleteTaskStep(id: number): Promise<void> {
  return request<void>(`/steps/${id}`, {
    method: 'DELETE'
  });
}

export function recommendTasks(payload: SupportRecommendRequest): Promise<TaskRecommendation[]> {
  return request<TaskRecommendation[]>('/support/recommend-tasks', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function getAIStatus(): Promise<AIStatus> {
  return request<AIStatus>('/ai/status');
}

export function aiEnrichTask(taskId: number): Promise<TaskEnrichment> {
  return request<TaskEnrichment>(`/ai/enrich-task/${taskId}`, { method: 'POST' });
}

export function aiBreakDownTask(taskId: number): Promise<TaskBreakdown> {
  return request<TaskBreakdown>(`/ai/break-down-task/${taskId}`, { method: 'POST' });
}

export function aiReflectSession(payload: { task_id: number; session_note: string; outcome?: string | null }): Promise<SessionReflection> {
  return request<SessionReflection>('/ai/reflect-session', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function aiPlanDay(payload: {
  date: string;
  energy: string;
  focus: string;
  available_minutes?: number | null;
  free_text?: string | null;
  preferred_context?: string | null;
}): Promise<PlannedDayProposal> {
  return request<PlannedDayProposal>('/ai/plan-day', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function getTaskAnalytics(taskId: number): Promise<TaskAnalytics> {
  return request<TaskAnalytics>(`/analytics/task/${taskId}`);
}

export function getContextAnalytics(context: string): Promise<ContextAnalytics> {
  return request<ContextAnalytics>(`/analytics/context/${context}`);
}

export function completeTask(id: number, payload: { completed_on?: string | null; source_block_id?: number | null }): Promise<Task> {
  return request<Task>(`/tasks/${id}/complete`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function getHabitStats(days: number): Promise<HabitStats[]> {
  return request<HabitStats[]>(`/tasks/habits/stats?days=${days}`);
}

export function getDayBlocks(date: string): Promise<DayBlock[]> {
  return request<DayBlock[]>(`/days/${date}/blocks`);
}

export function createDayBlock(date: string, payload: DayBlockCreate): Promise<DayBlock> {
  return request<DayBlock>(`/days/${date}/blocks`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function updateDayBlock(id: number, payload: DayBlockUpdate): Promise<DayBlock> {
  return request<DayBlock>(`/blocks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  });
}

export function deleteDayBlock(id: number): Promise<void> {
  return request<void>(`/blocks/${id}`, {
    method: 'DELETE'
  });
}

export function getTags(): Promise<Tag[]> {
  return request<Tag[]>('/tags');
}

export function createTag(payload: TagCreate): Promise<Tag> {
  return request<Tag>('/tags', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function getProjects(): Promise<Project[]> {
  return request<Project[]>('/projects');
}

export function createProject(payload: ProjectCreate): Promise<Project> {
  return request<Project>('/projects', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function getMilestones(): Promise<Milestone[]> {
  return request<Milestone[]>('/milestones');
}

export function createMilestone(payload: MilestoneCreate): Promise<Milestone> {
  return request<Milestone>('/milestones', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function getExternalCalendarStatus(): Promise<ExternalCalendarStatus[]> {
  return request<ExternalCalendarStatus[]>('/external-calendars/status');
}

export function disconnectCalendar(provider: 'google' | 'microsoft'): Promise<{ disconnected: boolean }> {
  return request<{ disconnected: boolean }>(`/auth/${provider}/disconnect`, {
    method: 'POST'
  });
}

export function getCalendarBlocks(date: string): Promise<ExternalCalendarBlock[]> {
  return request<ExternalCalendarBlock[]>(`/calendar-blocks/${date}`);
}

export function updateCalendarBlock(id: number, payload: { title?: string | null; busy_status?: string }): Promise<ExternalCalendarBlock> {
  return request<ExternalCalendarBlock>(`/calendar-blocks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  });
}

export function deleteCalendarBlock(id: number): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`/calendar-blocks/${id}`, {
    method: 'DELETE'
  });
}

export function getGitHubConfig(): Promise<GitHubConfig> {
  return request<GitHubConfig>('/github/config');
}

export function getGitHubMilestones(owner: string, repo: string): Promise<GitHubMilestone[]> {
  return request<GitHubMilestone[]>(`/github/repos/${owner}/${repo}/milestones`);
}

export function getGitHubMilestoneIssues(owner: string, repo: string, milestone: number): Promise<GitHubIssue[]> {
  return request<GitHubIssue[]>(`/github/repos/${owner}/${repo}/milestones/${milestone}/issues`);
}

export function importGitHubIssue(payload: ImportGitHubIssueRequest): Promise<Task> {
  return request<Task>('/github/import-issue', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function updateExternalWorkItem(id: number, payload: { ignored: boolean }): Promise<GitHubIssue> {
  return request<GitHubIssue>(`/external-work-items/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  });
}
