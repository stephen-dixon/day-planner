<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { getMilestones, getProjects, getTasks } from '$lib/api';
  import type { Milestone, Project, Task } from '$lib/types';

  const dayWidth = 36;

  let projects: Project[] = [];
  let milestones: Milestone[] = [];
  let tasks: Task[] = [];
  let error = '';

  $: projectId = Number($page.params.projectId);
  $: project = projects.find((item) => item.id === projectId);
  $: projectTasks = tasks.filter((task) => task.project_id === projectId);
  $: projectMilestones = milestones.filter((milestone) => milestone.project_id === projectId);
  $: timeline = buildTimeline(projectTasks, projectMilestones);

  function parseDate(value: string | null): Date | null {
    return value ? new Date(`${value}T00:00:00`) : null;
  }

  function isoDate(value: Date): string {
    return value.toISOString().slice(0, 10);
  }

  function addDays(value: Date, days: number): Date {
    const next = new Date(value);
    next.setDate(next.getDate() + days);
    return next;
  }

  function daysBetween(start: Date, end: Date): number {
    return Math.round((end.getTime() - start.getTime()) / 86_400_000);
  }

  function buildTimeline(items: Task[], milestoneItems: Milestone[]) {
    const dates = [
      ...items.flatMap((task) => [parseDate(task.planned_date), parseDate(task.due_date)]),
      ...milestoneItems.map((milestone) => parseDate(milestone.due_date))
    ].filter((value): value is Date => value !== null);

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const start = dates.length ? new Date(Math.min(...dates.map((date) => date.getTime()))) : today;
    const end = dates.length ? new Date(Math.max(...dates.map((date) => date.getTime()))) : addDays(today, 14);
    const paddedStart = addDays(start, -2);
    const paddedEnd = addDays(end, 4);
    const days = Array.from({ length: daysBetween(paddedStart, paddedEnd) + 1 }, (_, index) => addDays(paddedStart, index));
    return { start: paddedStart, end: paddedEnd, days };
  }

  function taskLeft(task: Task): number {
    const start = parseDate(task.planned_date) ?? parseDate(task.due_date) ?? timeline.start;
    return Math.max(0, daysBetween(timeline.start, start) * dayWidth);
  }

  function taskWidth(task: Task): number {
    const start = parseDate(task.planned_date) ?? parseDate(task.due_date) ?? timeline.start;
    const end = parseDate(task.due_date) ?? start;
    return Math.max(dayWidth, (daysBetween(start, end) + 1) * dayWidth);
  }

  function milestoneLeft(milestone: Milestone): number {
    const due = parseDate(milestone.due_date) ?? timeline.start;
    return Math.max(0, daysBetween(timeline.start, due) * dayWidth);
  }

  function milestoneName(id: number | null): string {
    return projectMilestones.find((milestone) => milestone.id === id)?.name ?? 'No milestone';
  }

  async function loadPage(): Promise<void> {
    try {
      const [projectResults, milestoneResults, taskResults] = await Promise.all([getProjects(), getMilestones(), getTasks()]);
      projects = projectResults;
      milestones = milestoneResults;
      tasks = taskResults;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load project gantt chart.';
    }
  }

  onMount(loadPage);
</script>

<svelte:head>
  <title>{project?.name ?? 'Project'} Gantt · Day Planner</title>
</svelte:head>

<main class="gantt-page">
  <div class="header">
    <div>
      <p class="eyebrow">Project timeline</p>
      <h1>{project?.name ?? 'Project'}</h1>
    </div>
    <a href="/projects">Back to projects</a>
  </div>

  {#if error}
    <p class="error">{error}</p>
  {/if}

  <section class="chart">
    <div class="date-row" style={`width: ${timeline.days.length * dayWidth}px;`}>
      {#each timeline.days as day}
        <span>{isoDate(day).slice(5)}</span>
      {/each}
    </div>

    <div class="milestone-layer" style={`width: ${timeline.days.length * dayWidth}px;`}>
      {#each projectMilestones.filter((milestone) => milestone.due_date) as milestone}
        <div class="milestone-marker" style={`left: ${milestoneLeft(milestone)}px;`}>
          <span>{milestone.name}</span>
        </div>
      {/each}
    </div>

    {#each projectTasks as task}
      <div class:done={task.status === 'done'} class="task-row">
        <div class="task-name">
          <strong>{task.title}</strong>
          <span>{milestoneName(task.milestone_id)} · {task.status}</span>
        </div>
        <div class="bar-area" style={`width: ${timeline.days.length * dayWidth}px;`}>
          <div class="task-bar" style={`left: ${taskLeft(task)}px; width: ${taskWidth(task)}px;`}>
            {task.planned_date ?? 'unscheduled'} → {task.due_date ?? 'no due date'}
          </div>
        </div>
      </div>
    {/each}
  </section>
</main>

<style>
  .gantt-page {
    display: grid;
    gap: 1rem;
    max-width: 1280px;
    margin: 0 auto;
    padding: 1rem;
  }

  .header {
    align-items: center;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
  }

  .header a {
    color: #1d5fb8;
    text-decoration: none;
  }

  .eyebrow {
    color: #687385;
    font-size: 0.78rem;
    font-weight: 700;
    margin: 0 0 0.2rem;
    text-transform: uppercase;
  }

  h1 {
    margin: 0;
  }

  .chart {
    background: #fff;
    border: 1px solid #d9e0e8;
    border-radius: 8px;
    overflow: auto;
    padding: 1rem;
  }

  .date-row {
    display: grid;
    grid-auto-columns: 36px;
    grid-auto-flow: column;
    margin-left: 260px;
  }

  .date-row span {
    border-left: 1px solid #edf1f5;
    color: #687385;
    font-size: 0.75rem;
    padding-bottom: 0.4rem;
    text-align: center;
  }

  .milestone-layer {
    height: 42px;
    margin-left: 260px;
    position: relative;
  }

  .milestone-marker {
    border-left: 2px solid #9b6b00;
    bottom: 0;
    color: #7a5400;
    font-size: 0.75rem;
    position: absolute;
    top: 0;
  }

  .milestone-marker span {
    background: #fff8e6;
    border: 1px solid #e2c46f;
    border-radius: 4px;
    display: inline-block;
    margin-left: 0.25rem;
    padding: 0.1rem 0.3rem;
    white-space: nowrap;
  }

  .task-row {
    align-items: center;
    border-top: 1px solid #edf1f5;
    display: grid;
    grid-template-columns: 260px 1fr;
    min-height: 54px;
  }

  .task-row.done {
    opacity: 0.62;
  }

  .task-name {
    display: grid;
    gap: 0.15rem;
    padding-right: 1rem;
  }

  .task-name span {
    color: #687385;
    font-size: 0.8rem;
  }

  .bar-area {
    background:
      repeating-linear-gradient(
        to right,
        transparent,
        transparent 35px,
        #edf1f5 36px
      );
    height: 34px;
    position: relative;
  }

  .task-bar {
    background: #e8f2ff;
    border: 1px solid #6aa6f8;
    border-left: 5px solid #2f80ed;
    border-radius: 6px;
    box-sizing: border-box;
    font-size: 0.78rem;
    height: 30px;
    overflow: hidden;
    padding: 0.35rem 0.45rem;
    position: absolute;
    top: 2px;
    white-space: nowrap;
  }

  .error {
    background: #fff0f0;
    border: 1px solid #e7a7a7;
    border-radius: 6px;
    color: #9d2525;
    padding: 0.7rem;
  }
</style>
