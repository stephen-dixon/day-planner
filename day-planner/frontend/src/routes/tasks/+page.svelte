<script lang="ts">
  import { onMount } from 'svelte';
  import {
    createMilestone,
    createProject,
    createTag,
    createTask,
    deleteTask,
    getGitHubConfig,
    getGitHubMilestoneIssues,
    getGitHubMilestones,
    getMilestones,
    getProjects,
    getTags,
    getTasks,
    importGitHubIssue,
    updateExternalWorkItem,
    updateTask
  } from '$lib/api';
  import type { GitHubIssue, GitHubMilestone, Milestone, Project, Tag, Task } from '$lib/types';

  let tasks: Task[] = [];
  let tags: Tag[] = [];
  let projects: Project[] = [];
  let milestones: Milestone[] = [];
  let loading = true;
  let saving = false;
  let error = '';
  let editingTaskId: number | null = null;
  let editDraft = {
    planned_date: '',
    due_date: '',
    estimated_minutes: 60,
    priority: 3,
    status: 'todo',
    project_id: '',
    milestone_id: '',
    is_recurring: false,
    recurrence_type: 'from_completion',
    recurrence_interval_days: 7,
    recurrence_min_days: 2,
    recurrence_max_days: 4,
    is_habit: false
  };

  let title = '';
  let notes = '';
  let plannedDate = '';
  let dueDate = '';
  let estimate = 60;
  let priority = 3;
  let selectedTagIds: number[] = [];
  let selectedProjectId = '';
  let selectedMilestoneId = '';
  let isRecurring = false;
  let isHabit = false;
  let recurrenceType = 'from_completion';
  let recurrenceIntervalDays = 7;
  let recurrenceMinDays = 2;
  let recurrenceMaxDays = 4;

  let tagName = '';
  let tagColor = '#2f80ed';
  let projectName = '';
  let projectNotes = '';
  let milestoneName = '';
  let milestoneDueDate = '';
  let milestoneProjectId = '';
  let githubOwner = '';
  let githubRepo = '';
  let githubMilestones: GitHubMilestone[] = [];
  let selectedGitHubMilestone = '';
  let githubIssues: GitHubIssue[] = [];
  let importEstimate = 60;
  let importPriority = 3;

  $: activeTasks = tasks.filter((task) => task.status !== 'done');
  $: projectMilestones = milestones.filter((milestone) => String(milestone.project_id) === selectedProjectId);
  $: editMilestones = milestones.filter((milestone) => String(milestone.project_id) === editDraft.project_id);
  $: backlogGroups = groupTasks(activeTasks);

  function groupTasks(items: Task[]): { label: string; tasks: Task[] }[] {
    const groups = new Map<string, Task[]>();
    for (const task of items) {
      const project = projects.find((item) => item.id === task.project_id);
      const milestone = milestones.find((item) => item.id === task.milestone_id);
      const label = project
        ? `${project.name}${milestone ? ` / ${milestone.name}` : ''}`
        : task.planned_date || 'Unscheduled';
      groups.set(label, [...(groups.get(label) ?? []), task]);
    }
    return [...groups.entries()].map(([label, groupedTasks]) => ({ label, tasks: groupedTasks }));
  }

  function taskAccent(task: Task): string {
    return task.tags[0]?.color ?? '#2f80ed';
  }

  function toggleTag(tagId: number): void {
    selectedTagIds = selectedTagIds.includes(tagId)
      ? selectedTagIds.filter((id) => id !== tagId)
      : [...selectedTagIds, tagId];
  }

  async function refreshData(): Promise<void> {
    error = '';
    const [taskResults, tagResults, projectResults, milestoneResults] = await Promise.all([
      getTasks(),
      getTags(),
      getProjects(),
      getMilestones()
    ]);
    tasks = taskResults;
    tags = tagResults;
    projects = projectResults;
    milestones = milestoneResults;
  }

  async function loadGitHubDefaults(): Promise<void> {
    try {
      const config = await getGitHubConfig();
      githubOwner = config.default_owner ?? '';
      githubRepo = config.default_repo ?? '';
    } catch {
      // The GitHub panel will show the explicit API error when the user loads data.
    }
  }

  async function loadPage(): Promise<void> {
    loading = true;
    try {
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load tasks.';
    } finally {
      loading = false;
    }
  }

  async function submitTask(): Promise<void> {
    if (!title.trim()) return;

    saving = true;
    error = '';
    try {
      await createTask({
        title: title.trim(),
        notes: notes.trim() || null,
        planned_date: plannedDate || null,
        due_date: dueDate || null,
        estimated_minutes: estimate || null,
        priority,
        tag_ids: selectedTagIds,
        project_id: selectedProjectId ? Number(selectedProjectId) : null,
        milestone_id: selectedMilestoneId ? Number(selectedMilestoneId) : null,
        is_recurring: isRecurring,
        is_habit: isHabit,
        recurrence_type: isRecurring ? recurrenceType : null,
        recurrence_interval_days: isRecurring ? recurrenceIntervalDays : null,
        recurrence_min_days: isHabit ? recurrenceMinDays : null,
        recurrence_max_days: isHabit ? recurrenceMaxDays : null
      });
      title = '';
      notes = '';
      plannedDate = '';
      dueDate = '';
      estimate = 60;
      priority = 3;
      selectedTagIds = [];
      selectedProjectId = '';
      selectedMilestoneId = '';
      isRecurring = false;
      isHabit = false;
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not create task.';
    } finally {
      saving = false;
    }
  }

  async function submitTag(): Promise<void> {
    if (!tagName.trim()) return;
    saving = true;
    error = '';
    try {
      await createTag({ name: tagName.trim(), color: tagColor });
      tagName = '';
      tagColor = '#2f80ed';
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not create tag.';
    } finally {
      saving = false;
    }
  }

  async function submitProject(): Promise<void> {
    if (!projectName.trim()) return;
    saving = true;
    error = '';
    try {
      const project = await createProject({ name: projectName.trim(), notes: projectNotes.trim() || null });
      selectedProjectId = String(project.id);
      milestoneProjectId = String(project.id);
      projectName = '';
      projectNotes = '';
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not create project.';
    } finally {
      saving = false;
    }
  }

  async function submitMilestone(): Promise<void> {
    if (!milestoneName.trim() || !milestoneProjectId) return;
    saving = true;
    error = '';
    try {
      await createMilestone({
        project_id: Number(milestoneProjectId),
        name: milestoneName.trim(),
        due_date: milestoneDueDate || null
      });
      milestoneName = '';
      milestoneDueDate = '';
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not create milestone.';
    } finally {
      saving = false;
    }
  }

  async function markDone(task: Task): Promise<void> {
    saving = true;
    error = '';
    try {
      await updateTask(task.id, { status: 'done' });
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not update task.';
    } finally {
      saving = false;
    }
  }

  function startEdit(task: Task): void {
    editingTaskId = task.id;
    editDraft = {
      planned_date: task.planned_date ?? '',
      due_date: task.due_date ?? '',
      estimated_minutes: task.estimated_minutes ?? 60,
      priority: task.priority,
      status: task.status,
      project_id: task.project_id ? String(task.project_id) : '',
      milestone_id: task.milestone_id ? String(task.milestone_id) : '',
      is_recurring: task.is_recurring,
      recurrence_type: task.recurrence_type ?? 'from_completion',
      recurrence_interval_days: task.recurrence_interval_days ?? 7,
      recurrence_min_days: task.recurrence_min_days ?? 2,
      recurrence_max_days: task.recurrence_max_days ?? 4,
      is_habit: task.is_habit
    };
  }

  async function saveEdit(task: Task): Promise<void> {
    saving = true;
    error = '';
    try {
      await updateTask(task.id, {
        planned_date: editDraft.planned_date || null,
        due_date: editDraft.due_date || null,
        estimated_minutes: editDraft.estimated_minutes || null,
        priority: editDraft.priority,
        status: editDraft.status,
        project_id: editDraft.project_id ? Number(editDraft.project_id) : null,
        milestone_id: editDraft.milestone_id ? Number(editDraft.milestone_id) : null,
        is_recurring: editDraft.is_recurring,
        is_habit: editDraft.is_habit,
        recurrence_type: editDraft.is_recurring ? editDraft.recurrence_type : null,
        recurrence_interval_days: editDraft.is_recurring ? editDraft.recurrence_interval_days : null,
        recurrence_min_days: editDraft.is_habit ? editDraft.recurrence_min_days : null,
        recurrence_max_days: editDraft.is_habit ? editDraft.recurrence_max_days : null
      });
      editingTaskId = null;
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not save task metadata.';
    } finally {
      saving = false;
    }
  }

  async function removeTask(task: Task): Promise<void> {
    if (!window.confirm(`Delete task "${task.title}"?`)) return;
    saving = true;
    error = '';
    try {
      await deleteTask(task.id);
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not delete task.';
    } finally {
      saving = false;
    }
  }

  async function loadGithubMilestones(): Promise<void> {
    if (!githubOwner.trim() || !githubRepo.trim()) return;
    saving = true;
    error = '';
    try {
      githubMilestones = await getGitHubMilestones(githubOwner.trim(), githubRepo.trim());
      selectedGitHubMilestone = githubMilestones[0] ? String(githubMilestones[0].number) : '';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load GitHub milestones.';
    } finally {
      saving = false;
    }
  }

  async function loadGithubIssues(): Promise<void> {
    if (!githubOwner.trim() || !githubRepo.trim() || !selectedGitHubMilestone) return;
    saving = true;
    error = '';
    try {
      githubIssues = await getGitHubMilestoneIssues(githubOwner.trim(), githubRepo.trim(), Number(selectedGitHubMilestone));
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load GitHub issues.';
    } finally {
      saving = false;
    }
  }

  async function importIssue(issue: GitHubIssue): Promise<void> {
    saving = true;
    error = '';
    try {
      await importGitHubIssue({
        owner: githubOwner.trim(),
        repo: githubRepo.trim(),
        issue_number: issue.number,
        estimated_minutes: importEstimate || null,
        priority: importPriority || null
      });
      await refreshData();
      await loadGithubIssues();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not import GitHub issue.';
    } finally {
      saving = false;
    }
  }

  async function ignoreIssue(issue: GitHubIssue): Promise<void> {
    if (!issue.external_work_item_id) return;
    saving = true;
    error = '';
    try {
      await updateExternalWorkItem(issue.external_work_item_id, { ignored: true });
      githubIssues = githubIssues.map((item) => item.external_work_item_id === issue.external_work_item_id ? { ...item, ignored: true } : item);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not ignore GitHub issue.';
    } finally {
      saving = false;
    }
  }

  onMount(async () => {
    await Promise.all([loadPage(), loadGitHubDefaults()]);
  });
</script>

<svelte:head>
  <title>Tasks · Day Planner</title>
</svelte:head>

<main class="tasks-page">
  <section class="composer">
    <div>
      <p class="eyebrow">Focused backlog</p>
      <h1>Create tasks</h1>
    </div>

    {#if error}
      <p class="error">{error}</p>
    {/if}
    {#if loading}
      <p class="status">Loading...</p>
    {/if}

    <form class="task-form" on:submit|preventDefault={submitTask}>
      <label>
        Title
        <input bind:value={title} placeholder="Draft project outline" />
      </label>
      <label>
        Notes
        <textarea bind:value={notes} rows="4"></textarea>
      </label>
      <div class="grid">
        <label>
          Planned date
          <input bind:value={plannedDate} type="date" />
        </label>
        <label>
          Due date
          <input bind:value={dueDate} type="date" />
        </label>
        <label>
          Estimate
          <input bind:value={estimate} min="15" step="15" type="number" />
        </label>
        <label>
          Priority
          <input bind:value={priority} min="1" max="5" type="number" />
        </label>
      </div>
      <div class="grid">
        <label>
          Project
          <select bind:value={selectedProjectId}>
            <option value="">None</option>
            {#each projects as project}
              <option value={project.id}>{project.name}</option>
            {/each}
          </select>
        </label>
        <label>
          Milestone
          <select bind:value={selectedMilestoneId} disabled={!selectedProjectId}>
            <option value="">None</option>
            {#each projectMilestones as milestone}
              <option value={milestone.id}>{milestone.name}</option>
            {/each}
          </select>
        </label>
      </div>
      <div class="tag-picker">
        <span>Tags</span>
        <div class="tag-row">
          {#each tags as tag}
            <button
              class:selected={selectedTagIds.includes(tag.id)}
              style={`--tag-color: ${tag.color};`}
              type="button"
              on:click={() => toggleTag(tag.id)}
            >
              {tag.name}
            </button>
          {/each}
        </div>
      </div>
      <div class="recurrence-box">
        <label class="check-row"><input bind:checked={isRecurring} type="checkbox" /> Recurring</label>
        <label class="check-row"><input bind:checked={isHabit} type="checkbox" /> Habit</label>
        {#if isRecurring}
          <label>
            Frequency
            <select bind:value={recurrenceType}>
              <option value="from_completion">From last complete</option>
              <option value="fixed_weekly">Fixed weekly</option>
            </select>
          </label>
          <label>
            Interval days
            <input bind:value={recurrenceIntervalDays} min="1" type="number" />
          </label>
          {#if isHabit}
            <div class="grid">
              <label>
                Min gap days
                <input bind:value={recurrenceMinDays} min="1" type="number" />
              </label>
              <label>
                Max gap days
                <input bind:value={recurrenceMaxDays} min="1" type="number" />
              </label>
            </div>
          {/if}
        {/if}
      </div>
      <button type="submit" disabled={saving || !title.trim()}>Create task</button>
    </form>
  </section>

  <aside class="metadata">
    <section>
      <h2>Tags</h2>
      <form class="inline-form" on:submit|preventDefault={submitTag}>
        <input bind:value={tagName} placeholder="Project category" />
        <input bind:value={tagColor} aria-label="Tag color" type="color" />
        <button type="submit" disabled={saving || !tagName.trim()}>Add</button>
      </form>
      <div class="tag-row">
        {#each tags as tag}
          <span class="tag-pill" style={`--tag-color: ${tag.color};`}>{tag.name}</span>
        {/each}
      </div>
    </section>

    <section>
      <h2>Projects</h2>
      <form class="stack-form" on:submit|preventDefault={submitProject}>
        <input bind:value={projectName} placeholder="Long-running project" />
        <textarea bind:value={projectNotes} rows="3" placeholder="Optional project notes"></textarea>
        <button type="submit" disabled={saving || !projectName.trim()}>Create project</button>
      </form>
    </section>

    <section>
      <h2>Milestones</h2>
      <form class="stack-form" on:submit|preventDefault={submitMilestone}>
        <select bind:value={milestoneProjectId}>
          <option value="">Choose project</option>
          {#each projects as project}
            <option value={project.id}>{project.name}</option>
          {/each}
        </select>
        <input bind:value={milestoneName} placeholder="Milestone name" />
        <input bind:value={milestoneDueDate} type="date" />
        <button type="submit" disabled={saving || !milestoneName.trim() || !milestoneProjectId}>Add milestone</button>
      </form>
    </section>

    <section>
      <h2>GitHub issues</h2>
      <div class="stack-form">
        <input bind:value={githubOwner} placeholder="Owner" />
        <input bind:value={githubRepo} placeholder="Repository" />
        <button type="button" on:click={loadGithubMilestones} disabled={saving || !githubOwner.trim() || !githubRepo.trim()}>
          Load milestones
        </button>
        <select bind:value={selectedGitHubMilestone}>
          <option value="">Choose milestone</option>
          {#each githubMilestones as milestone}
            <option value={milestone.number}>{milestone.title} ({milestone.open_issues})</option>
          {/each}
        </select>
        <div class="grid">
          <label>
            Import estimate
            <input bind:value={importEstimate} min="15" step="15" type="number" />
          </label>
          <label>
            Import priority
            <input bind:value={importPriority} min="1" max="5" type="number" />
          </label>
        </div>
        <button type="button" on:click={loadGithubIssues} disabled={saving || !selectedGitHubMilestone}>
          Load issues
        </button>
      </div>
      <div class="github-list">
        {#each githubIssues as issue}
          <article class:ignored={issue.ignored} class="github-issue">
            <a href={issue.url} target="_blank" rel="noreferrer">{issue.title}</a>
            <span>#{issue.number} · {issue.state}</span>
            <div class="label-row">
              {#each issue.labels as label}
                <small>{label}</small>
              {/each}
            </div>
            {#if issue.imported_task_id}
              <strong>Imported</strong>
            {:else if issue.ignored}
              <strong>Ignored</strong>
            {:else}
              <div class="issue-actions">
                <button type="button" on:click={() => importIssue(issue)}>Import as task</button>
                <button type="button" on:click={() => ignoreIssue(issue)}>Ignore</button>
              </div>
            {/if}
          </article>
        {/each}
      </div>
    </section>
  </aside>

  <section class="backlog">
    <div>
      <p class="eyebrow">Backlog</p>
      <h2>Active tasks</h2>
    </div>

    {#if activeTasks.length === 0}
      <p class="status">No active tasks.</p>
    {:else}
      {#each backlogGroups as group}
        <section class="group">
          <h3>{group.label}</h3>
          <div class="task-list">
            {#each group.tasks as task}
              <article class="task-card" style={`--task-color: ${taskAccent(task)};`}>
                <div>
                  <strong>{task.title}</strong>
                  <p>{task.notes || 'No notes'}</p>
                </div>
                <dl>
                  <div><dt>Planned</dt><dd>{task.planned_date ?? 'Unscheduled'}</dd></div>
                  <div><dt>Due</dt><dd>{task.due_date ?? 'None'}</dd></div>
                  <div><dt>Estimate</dt><dd>{task.estimated_minutes ?? 60} min</dd></div>
                </dl>
                <div class="tag-row">
                  {#each task.tags as tag}
                    <span class="tag-pill" style={`--tag-color: ${tag.color};`}>{tag.name}</span>
                  {/each}
                </div>
                {#if editingTaskId === task.id}
                  <div class="edit-panel">
                    <input bind:value={editDraft.planned_date} type="date" aria-label="Planned date" />
                    <input bind:value={editDraft.due_date} type="date" aria-label="Due date" />
                    <input bind:value={editDraft.estimated_minutes} min="15" step="15" type="number" aria-label="Estimate" />
                    <input bind:value={editDraft.priority} min="1" max="5" type="number" aria-label="Priority" />
                    <select bind:value={editDraft.project_id} aria-label="Project">
                      <option value="">No project</option>
                      {#each projects as project}
                        <option value={project.id}>{project.name}</option>
                      {/each}
                    </select>
                    <select bind:value={editDraft.milestone_id} aria-label="Milestone" disabled={!editDraft.project_id}>
                      <option value="">No milestone</option>
                      {#each editMilestones as milestone}
                        <option value={milestone.id}>{milestone.name}</option>
                      {/each}
                    </select>
                    <select bind:value={editDraft.status} aria-label="Status">
                      <option value="todo">todo</option>
                      <option value="active">active</option>
                      <option value="done">done</option>
                    </select>
                    <label class="check-row"><input bind:checked={editDraft.is_recurring} type="checkbox" /> Recurring</label>
                    <label class="check-row"><input bind:checked={editDraft.is_habit} type="checkbox" /> Habit</label>
                    {#if editDraft.is_recurring}
                      <select bind:value={editDraft.recurrence_type} aria-label="Frequency">
                        <option value="from_completion">From last complete</option>
                        <option value="fixed_weekly">Fixed weekly</option>
                      </select>
                      <input bind:value={editDraft.recurrence_interval_days} min="1" type="number" aria-label="Interval days" />
                    {/if}
                    {#if editDraft.is_habit}
                      <input bind:value={editDraft.recurrence_min_days} min="1" type="number" aria-label="Minimum gap days" />
                      <input bind:value={editDraft.recurrence_max_days} min="1" type="number" aria-label="Maximum gap days" />
                    {/if}
                    <button type="button" on:click={() => saveEdit(task)}>Save</button>
                    <button type="button" on:click={() => (editingTaskId = null)}>Cancel</button>
                  </div>
                {:else}
                  <div class="task-actions">
                    <button type="button" on:click={() => startEdit(task)}>Edit</button>
                    <button type="button" on:click={() => markDone(task)}>Done</button>
                    <button type="button" on:click={() => removeTask(task)}>Delete</button>
                  </div>
                {/if}
              </article>
            {/each}
          </div>
        </section>
      {/each}
    {/if}
  </section>
</main>

<style>
  .tasks-page {
    display: grid;
    grid-template-columns: minmax(360px, 1fr) 340px;
    gap: 1rem;
    max-width: 1320px;
    margin: 0 auto;
    padding: 1rem;
  }

  .composer,
  .metadata,
  .backlog {
    background: #fff;
    border: 1px solid #d9e0e8;
    border-radius: 8px;
    padding: 1rem;
  }

  .backlog {
    grid-column: 1 / -1;
  }

  .eyebrow {
    color: #687385;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0;
    margin: 0 0 0.2rem;
    text-transform: uppercase;
  }

  h1,
  h2,
  h3 {
    margin: 0 0 0.75rem;
  }

  .task-form,
  .stack-form,
  .metadata {
    display: grid;
    gap: 0.75rem;
  }

  label,
  .tag-picker {
    color: #4f5d6f;
    display: grid;
    font-size: 0.86rem;
    gap: 0.3rem;
  }

  .grid {
    display: grid;
    gap: 0.75rem;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .inline-form {
    display: grid;
    gap: 0.4rem;
    grid-template-columns: 1fr 48px auto;
  }

  .tag-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }

  .tag-row button {
    border-color: var(--tag-color);
  }

  .tag-row button.selected,
  .tag-pill {
    background: var(--tag-color);
    color: #fff;
  }

  .tag-pill {
    border-radius: 999px;
    font-size: 0.8rem;
    padding: 0.15rem 0.45rem;
  }

  .recurrence-box {
    border: 1px solid #edf1f5;
    border-radius: 6px;
    display: grid;
    gap: 0.6rem;
    padding: 0.7rem;
  }

  .check-row {
    align-items: center;
    display: flex;
    gap: 0.45rem;
  }

  .check-row input {
    width: auto;
  }

  .group {
    border-top: 1px solid #edf1f5;
    padding-top: 0.75rem;
  }

  .task-list {
    display: grid;
    gap: 0.75rem;
  }

  .task-card {
    border: 1px solid #cbd7e3;
    border-left: 5px solid var(--task-color);
    border-radius: 6px;
    display: grid;
    gap: 0.75rem;
    grid-template-columns: minmax(0, 1fr) auto auto auto auto;
    padding: 0.75rem;
  }

  .task-actions,
  .issue-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }

  .edit-panel {
    display: grid;
    gap: 0.35rem;
    min-width: 220px;
  }

  .github-list {
    display: grid;
    gap: 0.5rem;
    margin-top: 0.75rem;
  }

  .github-issue {
    border: 1px solid #d9e0e8;
    border-radius: 6px;
    display: grid;
    gap: 0.35rem;
    padding: 0.6rem;
  }

  .github-issue.ignored {
    opacity: 0.55;
  }

  .github-issue a {
    color: #1d5fb8;
    font-weight: 700;
    text-decoration: none;
  }

  .github-issue span {
    color: #596679;
    font-size: 0.84rem;
  }

  .label-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
  }

  .label-row small {
    background: #eef2f6;
    border-radius: 999px;
    padding: 0.15rem 0.45rem;
  }

  .task-card p {
    color: #566273;
    margin: 0.35rem 0 0;
  }

  dl {
    display: grid;
    gap: 0.25rem;
    margin: 0;
  }

  dt {
    color: #687385;
    font-size: 0.75rem;
  }

  dd {
    margin: 0;
  }

  .status {
    color: #596679;
  }

  .error {
    background: #fff0f0;
    border: 1px solid #e7a7a7;
    border-radius: 6px;
    color: #9d2525;
    padding: 0.7rem;
  }

  @media (max-width: 900px) {
    .tasks-page,
    .task-card {
      grid-template-columns: 1fr;
    }
  }
</style>
