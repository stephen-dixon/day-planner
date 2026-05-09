import type {
  DayBlock,
  DayBlockCreate,
  DayBlockUpdate,
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
  TaskUpdate
} from './types';

const API_BASE = 'http://127.0.0.1:8000';
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
  const response = await fetch(`${API_BASE}${path}`, {
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
