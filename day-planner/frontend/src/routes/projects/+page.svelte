<script lang="ts">
  import { onMount } from 'svelte';
  import { deleteTask, getMilestones, getProjects, getTasks, updateTask } from '$lib/api';
  import type { Milestone, Project, Task } from '$lib/types';

  let projects: Project[] = [];
  let milestones: Milestone[] = [];
  let tasks: Task[] = [];
  let error = '';
  let saving = false;
  let editingTaskId: number | null = null;
  let draft = {
    planned_date: '',
    due_date: '',
    estimated_minutes: 60,
    priority: 3,
    status: 'todo',
    project_id: '',
    milestone_id: ''
  };

  $: draftMilestones = milestones.filter((milestone) => String(milestone.project_id) === draft.project_id);

  function milestonesFor(project: Project): Milestone[] {
    return milestones.filter((milestone) => milestone.project_id === project.id);
  }

  function tasksFor(project: Project, milestoneId?: number): Task[] {
    return tasks.filter((task) => task.project_id === project.id && (milestoneId === undefined || task.milestone_id === milestoneId));
  }

  function startEdit(task: Task): void {
    editingTaskId = task.id;
    draft = {
      planned_date: task.planned_date ?? '',
      due_date: task.due_date ?? '',
      estimated_minutes: task.estimated_minutes ?? 60,
      priority: task.priority,
      status: task.status,
      project_id: task.project_id ? String(task.project_id) : '',
      milestone_id: task.milestone_id ? String(task.milestone_id) : ''
    };
  }

  async function refresh(): Promise<void> {
    const [projectResults, milestoneResults, taskResults] = await Promise.all([getProjects(), getMilestones(), getTasks()]);
    projects = projectResults;
    milestones = milestoneResults;
    tasks = taskResults;
  }

  async function saveTask(task: Task): Promise<void> {
    saving = true;
    error = '';
    try {
      await updateTask(task.id, {
        planned_date: draft.planned_date || null,
        due_date: draft.due_date || null,
        estimated_minutes: draft.estimated_minutes || null,
        priority: draft.priority,
        status: draft.status,
        project_id: draft.project_id ? Number(draft.project_id) : null,
        milestone_id: draft.milestone_id ? Number(draft.milestone_id) : null
      });
      editingTaskId = null;
      await refresh();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not save task.';
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
      await refresh();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not delete task.';
    } finally {
      saving = false;
    }
  }

  onMount(async () => {
    try {
      await refresh();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load projects.';
    }
  });
</script>

<svelte:head>
  <title>Projects · Day Planner</title>
</svelte:head>

<main class="projects-page">
  <div>
    <p class="eyebrow">Projects</p>
    <h1>Project tasks</h1>
  </div>

  {#if error}
    <p class="error">{error}</p>
  {/if}

  {#each projects as project}
    <section class="project">
      <div class="project-header">
        <h2>{project.name}</h2>
        <a href={`/projects/${project.id}/gantt`}>Gantt chart</a>
      </div>
      {#if project.notes}
        <p>{project.notes}</p>
      {/if}

      <section class="milestone">
        <h3>Unassigned milestone</h3>
        {@render TaskList({ items: tasksFor(project).filter((task) => task.milestone_id === null) })}
      </section>

      {#each milestonesFor(project) as milestone}
        <section class="milestone">
          <h3>{milestone.name}</h3>
          {@render TaskList({ items: tasksFor(project, milestone.id) })}
        </section>
      {/each}
    </section>
  {/each}
</main>

{#snippet TaskList({ items }: { items: Task[] })}
  {#if items.length === 0}
    <p class="status">No tasks.</p>
  {:else}
    <div class="task-list">
      {#each items as task}
        <article class:done={task.status === 'done'} class="task-card">
          <div>
            <strong>{task.title}</strong>
            <p>{task.notes || 'No notes'}</p>
          </div>
          {#if editingTaskId === task.id}
            <div class="edit-panel">
              <input bind:value={draft.planned_date} type="date" aria-label="Planned date" />
              <input bind:value={draft.due_date} type="date" aria-label="Due date" />
              <input bind:value={draft.estimated_minutes} min="15" step="15" type="number" aria-label="Estimate" />
              <input bind:value={draft.priority} min="1" max="5" type="number" aria-label="Priority" />
              <select bind:value={draft.project_id} aria-label="Project">
                <option value="">No project</option>
                {#each projects as project}
                  <option value={project.id}>{project.name}</option>
                {/each}
              </select>
              <select bind:value={draft.milestone_id} aria-label="Milestone" disabled={!draft.project_id}>
                <option value="">No milestone</option>
                {#each draftMilestones as milestone}
                  <option value={milestone.id}>{milestone.name}</option>
                {/each}
              </select>
              <select bind:value={draft.status} aria-label="Status">
                <option value="todo">todo</option>
                <option value="active">active</option>
                <option value="done">done</option>
              </select>
              <button type="button" on:click={() => saveTask(task)} disabled={saving}>Save</button>
              <button type="button" on:click={() => (editingTaskId = null)}>Cancel</button>
            </div>
          {:else}
            <dl>
              <div><dt>Status</dt><dd>{task.status}</dd></div>
              <div><dt>Planned</dt><dd>{task.planned_date ?? 'Unscheduled'}</dd></div>
              <div><dt>Due</dt><dd>{task.due_date ?? 'None'}</dd></div>
            </dl>
            <div class="actions">
              <button type="button" on:click={() => startEdit(task)}>Edit</button>
              <button type="button" on:click={() => removeTask(task)}>Delete</button>
            </div>
          {/if}
        </article>
      {/each}
    </div>
  {/if}
{/snippet}

<style>
  .projects-page {
    display: grid;
    gap: 1rem;
    max-width: 1120px;
    margin: 0 auto;
    padding: 1rem;
  }

  .project,
  .milestone {
    background: #fff;
    border: 1px solid #d9e0e8;
    border-radius: 8px;
    padding: 1rem;
  }

  .milestone {
    margin-top: 0.75rem;
  }

  .eyebrow {
    color: #687385;
    font-size: 0.78rem;
    font-weight: 700;
    margin: 0 0 0.2rem;
    text-transform: uppercase;
  }

  h1,
  h2,
  h3 {
    margin: 0 0 0.75rem;
  }

  .project-header {
    align-items: center;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
  }

  .project-header a {
    color: #1d5fb8;
    text-decoration: none;
  }

  .task-list {
    display: grid;
    gap: 0.75rem;
  }

  .task-card {
    border: 1px solid #cbd7e3;
    border-left: 5px solid #2f80ed;
    border-radius: 6px;
    display: grid;
    gap: 0.75rem;
    grid-template-columns: minmax(0, 1fr) auto auto;
    padding: 0.75rem;
  }

  .task-card.done {
    border-left-color: #2f8f45;
    opacity: 0.75;
  }

  .task-card p,
  .status {
    color: #596679;
  }

  dl,
  .edit-panel {
    display: grid;
    gap: 0.35rem;
    margin: 0;
  }

  dt {
    color: #687385;
    font-size: 0.75rem;
  }

  dd {
    margin: 0;
  }

  .actions {
    display: flex;
    gap: 0.35rem;
  }

  .error {
    background: #fff0f0;
    border: 1px solid #e7a7a7;
    border-radius: 6px;
    color: #9d2525;
    padding: 0.7rem;
  }

  @media (max-width: 800px) {
    .task-card {
      grid-template-columns: 1fr;
    }
  }
</style>
