<script lang="ts">
  import { onMount } from 'svelte';
  import {
    apiUrl,
    createDayBlock,
    createTag,
    createTask,
    completeTask,
    deleteDayBlock,
    deleteCalendarBlock,
    disconnectCalendar,
    getCalendarBlocks,
    getDayBlocks,
    getExternalCalendarStatus,
    getMilestones,
    getProjects,
    getTags,
    getTasks,
    updateCalendarBlock,
    updateDayBlock,
    updateTask
  } from '$lib/api';
  import { minutesToTimeLabel, snapToIncrement, timeLabelToMinutes, todayISODate } from '$lib/time';
  import type { DayBlock, ExternalCalendarBlock, ExternalCalendarStatus, Milestone, Project, Tag, Task } from '$lib/types';

  const dayStart = 7 * 60;
  const dayEnd = 22 * 60;
  const dayMinutes = dayEnd - dayStart;
  const timelineHeight = 900;
  const pixelsPerMinute = timelineHeight / dayMinutes;
  const minimumDuration = 15;

  let selectedDate = todayISODate();
  let tasks: Task[] = [];
  let blocks: DayBlock[] = [];
  let tags: Tag[] = [];
  let projects: Project[] = [];
  let milestones: Milestone[] = [];
  let externalBlocks: ExternalCalendarBlock[] = [];
  let calendarStatuses: ExternalCalendarStatus[] = [];
  let externalLabels: Record<number, string> = {};
  let loading = true;
  let saving = false;
  let error = '';
  let expandedBlockId: number | null = null;

  let newTaskTitle = '';
  let newTaskNotes = '';
  let newTaskEstimate = 60;
  let newTaskPlannedDate = selectedDate;
  let newTaskDueDate = '';
  let newTaskTagIds: number[] = [];
  let newTaskRecurring = false;
  let newTaskHabit = false;
  let newTaskRecurrenceType = 'from_completion';
  let newTaskIntervalDays = 7;
  let newTaskMinDays = 2;
  let newTaskMaxDays = 4;
  let newTaskWeekdays: number[] = [];
  let newTagName = '';
  let newTagColor = '#2f80ed';

  let manualTimes: Record<number, { start: string; end: string }> = {};

  $: activeTasks = tasks.filter((task) => task.status !== 'done');
  $: backlogGroups = groupTasksByPlannedDate(activeTasks);
  $: hours = Array.from({ length: 16 }, (_, index) => dayStart + index * 60);

  function groupTasksByPlannedDate(items: Task[]): { label: string; tasks: Task[] }[] {
    const groups = new Map<string, Task[]>();
    for (const task of items) {
      const key = task.planned_date || 'Unscheduled';
      groups.set(key, [...(groups.get(key) ?? []), task]);
    }
    return [...groups.entries()]
      .sort(([left], [right]) => {
        if (left === 'Unscheduled') return 1;
        if (right === 'Unscheduled') return -1;
        return left.localeCompare(right);
      })
      .map(([label, groupedTasks]) => ({ label, tasks: groupedTasks }));
  }

  function taskForBlock(block: DayBlock): Task | undefined {
    return tasks.find((task) => task.id === block.task_id);
  }

  function projectName(projectId: number | null): string {
    return projects.find((project) => project.id === projectId)?.name ?? 'No project';
  }

  function milestoneName(milestoneId: number | null): string {
    return milestones.find((milestone) => milestone.id === milestoneId)?.name ?? 'No milestone';
  }

  function taskAccent(task: Task | undefined): string {
    return task?.tags[0]?.color ?? '#2f80ed';
  }

  function blockTop(block: { start_minute: number }): number {
    return (block.start_minute - dayStart) * pixelsPerMinute;
  }

  function blockHeight(block: { start_minute: number; end_minute: number }): number {
    return Math.max(minimumDuration * pixelsPerMinute, (block.end_minute - block.start_minute) * pixelsPerMinute);
  }

  function providerLabel(provider: string): string {
    return provider === 'microsoft' ? 'Outlook' : 'Google';
  }

  function overlapsExternal(start: number, end: number): boolean {
    return externalBlocks.some((block) => block.busy_status !== 'non_blocking' && start < block.end_minute && end > block.start_minute);
  }

  function confirmIfOverlapping(start: number, end: number): boolean {
    if (!overlapsExternal(start, end)) return true;
    return window.confirm('This overlaps a calendar event. Schedule anyway?');
  }

  function clampStart(startMinute: number, duration: number): number {
    return Math.min(Math.max(startMinute, dayStart), dayEnd - duration);
  }

  function minuteFromDrop(event: DragEvent, duration: number): number {
    const target = event.currentTarget as HTMLElement;
    const rect = target.getBoundingClientRect();
    const offsetY = event.clientY - rect.top;
    const rawMinute = dayStart + offsetY / pixelsPerMinute;
    return clampStart(snapToIncrement(rawMinute), duration);
  }

  function syncManualTimes(nextBlocks: DayBlock[]): void {
    manualTimes = Object.fromEntries(
      nextBlocks.map((block) => [
        block.id,
        {
          start: minutesToTimeLabel(block.start_minute),
          end: minutesToTimeLabel(block.end_minute)
        }
      ])
    );
  }

  function syncExternalLabels(nextBlocks: ExternalCalendarBlock[]): void {
    externalLabels = Object.fromEntries(nextBlocks.map((block) => [block.id, block.title ?? 'Busy']));
  }

  async function refreshData(): Promise<void> {
    error = '';
    const [taskResults, blockResults, calendarResults, statusResults, tagResults, projectResults, milestoneResults] = await Promise.all([
      getTasks(),
      getDayBlocks(selectedDate),
      getCalendarBlocks(selectedDate),
      getExternalCalendarStatus(),
      getTags(),
      getProjects(),
      getMilestones()
    ]);
    tasks = taskResults;
    blocks = blockResults;
    externalBlocks = calendarResults;
    calendarStatuses = statusResults;
    tags = tagResults;
    projects = projectResults;
    milestones = milestoneResults;
    syncManualTimes(blockResults);
    syncExternalLabels(calendarResults);
  }

  async function loadPage(): Promise<void> {
    loading = true;
    try {
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load planner data.';
    } finally {
      loading = false;
    }
  }

  async function submitTask(): Promise<void> {
    if (!newTaskTitle.trim()) return;

    saving = true;
    error = '';
    try {
      await createTask({
        title: newTaskTitle.trim(),
        notes: newTaskNotes.trim() || null,
        estimated_minutes: newTaskEstimate || null,
        planned_date: newTaskPlannedDate || null,
        due_date: newTaskDueDate || null,
        tag_ids: newTaskTagIds,
        is_recurring: newTaskRecurring,
        is_habit: newTaskHabit,
        recurrence_type: newTaskRecurring ? newTaskRecurrenceType : null,
        recurrence_interval_days: newTaskRecurrenceType === 'from_completion' ? newTaskIntervalDays : null,
        recurrence_weekdays: newTaskRecurrenceType === 'fixed_weekly' ? newTaskWeekdays : [],
        recurrence_min_days: newTaskHabit ? newTaskMinDays : null,
        recurrence_max_days: newTaskHabit ? newTaskMaxDays : null
      });
      newTaskTitle = '';
      newTaskNotes = '';
      newTaskEstimate = 60;
      newTaskPlannedDate = selectedDate;
      newTaskDueDate = '';
      newTaskTagIds = [];
      newTaskRecurring = false;
      newTaskHabit = false;
      newTaskWeekdays = [];
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not create task.';
    } finally {
      saving = false;
    }
  }

  async function submitTag(): Promise<void> {
    if (!newTagName.trim()) return;

    saving = true;
    error = '';
    try {
      const tag = await createTag({ name: newTagName.trim(), color: newTagColor });
      newTaskTagIds = [...newTaskTagIds, tag.id];
      newTagName = '';
      newTagColor = '#2f80ed';
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not create tag.';
    } finally {
      saving = false;
    }
  }

  function toggleNewTaskTag(tagId: number): void {
    newTaskTagIds = newTaskTagIds.includes(tagId)
      ? newTaskTagIds.filter((id) => id !== tagId)
      : [...newTaskTagIds, tagId];
  }

  function toggleNewTaskWeekday(day: number): void {
    newTaskWeekdays = newTaskWeekdays.includes(day)
      ? newTaskWeekdays.filter((item) => item !== day)
      : [...newTaskWeekdays, day].sort();
  }

  function dragTask(event: DragEvent, task: Task): void {
    event.dataTransfer?.setData('application/day-planner-task-id', String(task.id));
    event.dataTransfer?.setData('text/plain', String(task.id));
  }

  function dragBlock(event: DragEvent, block: DayBlock): void {
    event.dataTransfer?.setData('application/day-planner-block-id', String(block.id));
    event.dataTransfer?.setData('text/plain', String(block.id));
  }

  async function dropOnTimeline(event: DragEvent): Promise<void> {
    event.preventDefault();
    const taskIdText = event.dataTransfer?.getData('application/day-planner-task-id');
    const blockIdText = event.dataTransfer?.getData('application/day-planner-block-id');

    saving = true;
    error = '';
    try {
      if (taskIdText) {
        const task = tasks.find((item) => item.id === Number(taskIdText));
        if (!task) return;

        const duration = task.estimated_minutes ?? 60;
        const start = minuteFromDrop(event, duration);
        if (!confirmIfOverlapping(start, start + duration)) return;
        await createDayBlock(selectedDate, {
          task_id: task.id,
          start_minute: start,
          end_minute: start + duration
        });
        await updateTask(task.id, { planned_date: selectedDate });
      } else if (blockIdText) {
        const block = blocks.find((item) => item.id === Number(blockIdText));
        if (!block) return;

        const duration = block.end_minute - block.start_minute;
        const start = minuteFromDrop(event, duration);
        if (!confirmIfOverlapping(start, start + duration)) return;
        await updateDayBlock(block.id, {
          start_minute: start,
          end_minute: start + duration
        });
      }

      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not update planner.';
    } finally {
      saving = false;
    }
  }

  async function applyManualTime(block: DayBlock): Promise<void> {
    const time = manualTimes[block.id];
    if (!time) return;

    saving = true;
    error = '';
    try {
      const start = timeLabelToMinutes(time.start);
      const end = timeLabelToMinutes(time.end);
      if (end - start < minimumDuration) {
        throw new Error('Duration must be at least 15 minutes.');
      }
      if (!confirmIfOverlapping(start, end)) return;
      await updateDayBlock(block.id, { start_minute: start, end_minute: end });
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not save manual time.';
    } finally {
      saving = false;
    }
  }

  async function changeDuration(block: DayBlock, delta: number): Promise<void> {
    const nextEnd = block.end_minute + delta;
    if (nextEnd - block.start_minute < minimumDuration || nextEnd > 24 * 60) return;
    if (!confirmIfOverlapping(block.start_minute, nextEnd)) return;

    saving = true;
    error = '';
    try {
      await updateDayBlock(block.id, { end_minute: nextEnd });
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not change duration.';
    } finally {
      saving = false;
    }
  }

  async function markDone(block: DayBlock): Promise<void> {
    saving = true;
    error = '';
    try {
      await updateDayBlock(block.id, { status: 'done' });
      if (block.task_id) {
        await completeTask(block.task_id, { completed_on: block.date, source_block_id: block.id });
      }
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not mark block done.';
    } finally {
      saving = false;
    }
  }

  async function removeBlock(block: DayBlock): Promise<void> {
    saving = true;
    error = '';
    try {
      await deleteDayBlock(block.id);
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not remove block.';
    } finally {
      saving = false;
    }
  }

  async function disconnectProvider(provider: 'google' | 'microsoft'): Promise<void> {
    saving = true;
    error = '';
    try {
      await disconnectCalendar(provider);
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : `Could not disconnect ${provider}.`;
    } finally {
      saving = false;
    }
  }

  async function saveExternalLabel(block: ExternalCalendarBlock): Promise<void> {
    saving = true;
    error = '';
    try {
      await updateCalendarBlock(block.id, { title: externalLabels[block.id]?.trim() || 'Busy' });
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not update calendar block label.';
    } finally {
      saving = false;
    }
  }

  async function toggleExternalBlocking(block: ExternalCalendarBlock): Promise<void> {
    saving = true;
    error = '';
    try {
      await updateCalendarBlock(block.id, {
        busy_status: block.busy_status === 'non_blocking' ? 'busy' : 'non_blocking'
      });
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not update calendar block status.';
    } finally {
      saving = false;
    }
  }

  async function removeExternalBlock(block: ExternalCalendarBlock): Promise<void> {
    if (!window.confirm(`Hide ${providerLabel(block.provider)} calendar block?`)) return;
    saving = true;
    error = '';
    try {
      await deleteCalendarBlock(block.id);
      await refreshData();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not hide calendar block.';
    } finally {
      saving = false;
    }
  }

  onMount(loadPage);
</script>

<svelte:head>
  <title>Day Planner</title>
</svelte:head>

<main class="app-shell">
  <section class="backlog">
    <div class="panel-header">
      <div>
        <p class="eyebrow">Backlog</p>
        <h1>Tasks</h1>
      </div>
      <a class="secondary-link" href="/tasks">Focused view</a>
    </div>

    <form class="task-form" on:submit|preventDefault={submitTask}>
      <label>
        Task title
        <input bind:value={newTaskTitle} placeholder="Plan tomorrow" />
      </label>
      <label>
        Notes
        <textarea bind:value={newTaskNotes} rows="3" placeholder="Optional details"></textarea>
      </label>
      <div class="form-grid">
        <label>
          Planned date
          <input bind:value={newTaskPlannedDate} type="date" />
        </label>
        <label>
          Due date
          <input bind:value={newTaskDueDate} type="date" />
        </label>
        <label>
          Estimate
          <input bind:value={newTaskEstimate} min="15" step="15" type="number" />
        </label>
      </div>

      <div class="tag-picker">
        <span>Tags</span>
        <div class="tag-row">
          {#each tags as tag}
            <button
              class:selected={newTaskTagIds.includes(tag.id)}
              style={`--tag-color: ${tag.color};`}
              type="button"
              on:click={() => toggleNewTaskTag(tag.id)}
            >
              {tag.name}
            </button>
          {/each}
        </div>
      </div>

      <div class="recurrence-box">
        <label class="check-row">
          <input bind:checked={newTaskRecurring} type="checkbox" />
          Recurring task
        </label>
        <label class="check-row">
          <input bind:checked={newTaskHabit} type="checkbox" />
          Habit
        </label>
        {#if newTaskRecurring}
          <label>
            Frequency
            <select bind:value={newTaskRecurrenceType}>
              <option value="from_completion">From last complete</option>
              <option value="fixed_weekly">Fixed weekly</option>
            </select>
          </label>
          {#if newTaskRecurrenceType === 'from_completion'}
            <label>
              Every N days
              <input bind:value={newTaskIntervalDays} min="1" type="number" />
            </label>
          {:else}
            <div class="weekday-row">
              {#each ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as label, index}
                <button
                  class:selected={newTaskWeekdays.includes(index)}
                  type="button"
                  on:click={() => toggleNewTaskWeekday(index)}
                >
                  {label}
                </button>
              {/each}
            </div>
          {/if}
          {#if newTaskHabit}
            <div class="form-grid">
              <label>
                Min gap days
                <input bind:value={newTaskMinDays} min="1" type="number" />
              </label>
              <label>
                Max gap days
                <input bind:value={newTaskMaxDays} min="1" type="number" />
              </label>
            </div>
          {/if}
        {/if}
      </div>

      <div class="inline-create">
        <input bind:value={newTagName} placeholder="New tag" />
        <input bind:value={newTagColor} type="color" aria-label="Tag color" />
        <button type="button" on:click={submitTag} disabled={saving || !newTagName.trim()}>Add tag</button>
      </div>

      <button type="submit" disabled={saving || !newTaskTitle.trim()}>Create task</button>
    </form>

    {#if activeTasks.length === 0}
      <p class="empty">No active tasks yet.</p>
    {:else}
      {#each backlogGroups as group}
        <section class="backlog-group">
          <h2>{group.label}</h2>
          <div class="task-list">
            {#each group.tasks as task}
              <article
                class="task-card"
                draggable="true"
                style={`--task-color: ${taskAccent(task)};`}
                on:dragstart={(event) => dragTask(event, task)}
              >
                <strong>{task.title}</strong>
                {#if task.notes}
                  <p>{task.notes}</p>
                {/if}
                <span>{task.estimated_minutes ?? 60} min · due {task.due_date ?? 'none'}</span>
                <div class="tag-list">
                  {#each task.tags as tag}
                    <small style={`--tag-color: ${tag.color};`}>{tag.name}</small>
                  {/each}
                </div>
              </article>
            {/each}
          </div>
        </section>
      {/each}
    {/if}
  </section>

  <section class="planner">
    <div class="panel-header">
      <div>
        <p class="eyebrow">Today</p>
        <h2>Day planner</h2>
      </div>
      <label class="date-picker">
        Date
        <input bind:value={selectedDate} type="date" on:change={loadPage} />
      </label>
    </div>

    {#if loading}
      <p class="status">Loading planner...</p>
    {/if}
    {#if saving}
      <p class="status">Saving...</p>
    {/if}
    {#if error}
      <p class="error">{error}</p>
    {/if}

    <section class="calendar-settings">
      <div>
        <p class="eyebrow">Calendar integrations</p>
        <h3>Read-only busy blocks</h3>
      </div>
      <div class="calendar-statuses">
        {#each calendarStatuses as status}
          <div class="calendar-status">
            <strong>{providerLabel(status.provider)}</strong>
            <span>{status.connected ? status.account_email ?? 'Connected' : 'Not connected'}</span>
            {#if status.connected}
              <button type="button" on:click={() => disconnectProvider(status.provider === 'microsoft' ? 'microsoft' : 'google')}>
                Disconnect
              </button>
            {:else}
              <a class="button-link" href={apiUrl(`/auth/${status.provider}/start`)}>
                Connect {providerLabel(status.provider)}
              </a>
            {/if}
          </div>
        {/each}
      </div>
    </section>

    {#if expandedBlockId}
      {@const block = blocks.find((item) => item.id === expandedBlockId)}
      {@const task = block ? taskForBlock(block) : undefined}
      {#if block && task}
        <aside class="focus-panel">
          <div>
            <p class="eyebrow">Focused task</p>
            <h3>{task.title}</h3>
          </div>
          <p>{task.notes || 'No notes yet.'}</p>
          <dl>
            <div><dt>Time</dt><dd>{minutesToTimeLabel(block.start_minute)}-{minutesToTimeLabel(block.end_minute)}</dd></div>
            <div><dt>Due</dt><dd>{task.due_date ?? 'None'}</dd></div>
            <div><dt>Project</dt><dd>{projectName(task.project_id)}</dd></div>
            <div><dt>Milestone</dt><dd>{milestoneName(task.milestone_id)}</dd></div>
          </dl>
          <div class="tag-list">
            {#each task.tags as tag}
              <small style={`--tag-color: ${tag.color};`}>{tag.name}</small>
            {/each}
          </div>
          <button type="button" on:click={() => (expandedBlockId = null)}>Close</button>
        </aside>
      {/if}
    {/if}

    <div
      aria-label="Day timeline drop area"
      class="timeline"
      role="application"
      style={`height: ${timelineHeight}px;`}
      on:dragover|preventDefault
      on:drop={dropOnTimeline}
    >
      {#each hours as hour}
        <div class="hour-row" style={`top: ${(hour - dayStart) * pixelsPerMinute}px;`}>
          <span>{minutesToTimeLabel(hour)}</span>
        </div>
      {/each}

      {#each externalBlocks as block}
        <article
          aria-label={`${providerLabel(block.provider)} busy block`}
          class:non-blocking={block.busy_status === 'non_blocking'}
          class="external-block"
          style={`top: ${blockTop(block)}px; height: ${blockHeight(block)}px;`}
        >
          <div class="block-copy">
            <strong>{providerLabel(block.provider)}: {block.title ?? 'Busy'}</strong>
            <span>
              {minutesToTimeLabel(block.start_minute)}-{minutesToTimeLabel(block.end_minute)}
              {block.busy_status === 'non_blocking' ? ' · non-blocking' : ''}
            </span>
          </div>
          <div class="external-controls">
            <input bind:value={externalLabels[block.id]} aria-label="Calendar block label" />
            <button type="button" on:click={() => saveExternalLabel(block)}>Label</button>
            <button type="button" on:click={() => toggleExternalBlocking(block)}>
              {block.busy_status === 'non_blocking' ? 'Make blocking' : 'Non-blocking'}
            </button>
            <button type="button" on:click={() => removeExternalBlock(block)}>Hide</button>
          </div>
        </article>
      {/each}

      {#each blocks as block}
        {@const task = taskForBlock(block)}
        <article
          class:done={block.status === 'done'}
          class="scheduled-block"
          draggable="true"
          style={`top: ${blockTop(block)}px; height: ${blockHeight(block)}px; --task-color: ${taskAccent(task)};`}
          on:dragstart={(event) => dragBlock(event, block)}
        >
          <div class="block-copy">
            <strong>{task?.title ?? `Task ${block.task_id}`}</strong>
            <span>{minutesToTimeLabel(block.start_minute)}-{minutesToTimeLabel(block.end_minute)}</span>
          </div>
          {#if manualTimes[block.id]}
            <div class="manual-time">
              <input bind:value={manualTimes[block.id].start} aria-label="Start time" />
              <input bind:value={manualTimes[block.id].end} aria-label="End time" />
              <button type="button" on:click={() => applyManualTime(block)}>Set</button>
            </div>
          {/if}
          <div class="block-actions">
            <button type="button" on:click={() => changeDuration(block, 15)}>+15m</button>
            <button type="button" on:click={() => changeDuration(block, -15)}>-15m</button>
            <button type="button" on:click={() => (expandedBlockId = block.id)}>Details</button>
            <button type="button" on:click={() => markDone(block)}>Done</button>
            <button type="button" on:click={() => removeBlock(block)}>Remove</button>
          </div>
        </article>
      {/each}
    </div>
  </section>
</main>

<style>
  .app-shell {
    display: grid;
    grid-template-columns: 370px minmax(560px, 1fr);
    gap: 1rem;
    max-width: 1380px;
    margin: 0 auto;
    padding: 1rem;
  }

  .backlog,
  .planner,
  .focus-panel {
    background: #fff;
    border: 1px solid #d9e0e8;
    border-radius: 8px;
    padding: 1rem;
  }

  .panel-header {
    align-items: center;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  h1,
  h2,
  h3 {
    margin: 0;
  }

  .panel-header h1,
  .panel-header h2 {
    font-size: 1.35rem;
  }

  .eyebrow {
    color: #687385;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0;
    margin: 0 0 0.2rem;
    text-transform: uppercase;
  }

  .secondary-link {
    color: #1d5fb8;
    font-size: 0.9rem;
    text-decoration: none;
  }

  .task-form {
    display: grid;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  label,
  .tag-picker {
    color: #4f5d6f;
    display: grid;
    font-size: 0.86rem;
    gap: 0.3rem;
  }

  .form-grid {
    display: grid;
    gap: 0.6rem;
    grid-template-columns: 1fr 1fr;
  }

  .form-grid label:last-child {
    grid-column: 1 / -1;
  }

  .inline-create {
    display: grid;
    gap: 0.4rem;
    grid-template-columns: 1fr 48px auto;
  }

  .tag-row,
  .tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }

  .tag-row button {
    border-color: var(--tag-color);
  }

  .tag-row button.selected {
    background: var(--tag-color);
    color: #fff;
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

  .weekday-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
  }

  .weekday-row button.selected {
    background: #2f80ed;
    color: #fff;
  }

  .tag-list small {
    background: var(--tag-color);
    border-radius: 999px;
    color: #fff;
    padding: 0.15rem 0.45rem;
  }

  .backlog-group {
    border-top: 1px solid #edf1f5;
    padding-top: 0.75rem;
  }

  .backlog-group h2 {
    color: #405064;
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
  }

  .task-list {
    display: grid;
    gap: 0.75rem;
  }

  .task-card {
    border: 1px solid #cbd7e3;
    border-left: 5px solid var(--task-color);
    border-radius: 6px;
    cursor: grab;
    padding: 0.75rem;
  }

  .task-card p {
    color: #566273;
    margin: 0.35rem 0;
  }

  .task-card span,
  .block-copy span {
    color: #596679;
    font-size: 0.83rem;
  }

  .focus-panel {
    margin-bottom: 1rem;
  }

  .calendar-settings {
    border: 1px solid #d9e0e8;
    border-radius: 8px;
    margin-bottom: 1rem;
    padding: 0.75rem;
  }

  .calendar-statuses {
    display: grid;
    gap: 0.5rem;
  }

  .calendar-status {
    align-items: center;
    display: grid;
    gap: 0.5rem;
    grid-template-columns: 100px minmax(0, 1fr) auto;
  }

  .calendar-status span {
    color: #596679;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .button-link {
    border: 1px solid #c9d2dc;
    border-radius: 6px;
    color: #1f2933;
    padding: 0.45rem 0.65rem;
    text-decoration: none;
  }

  .focus-panel dl {
    display: grid;
    gap: 0.4rem;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .focus-panel dt {
    color: #687385;
    font-size: 0.78rem;
  }

  .focus-panel dd {
    margin: 0;
  }

  .timeline {
    background:
      repeating-linear-gradient(
        to bottom,
        transparent,
        transparent 14px,
        #eef2f6 15px
      );
    border: 1px solid #cbd7e3;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
  }

  .hour-row {
    border-top: 1px solid #aebdcb;
    box-sizing: border-box;
    color: #607086;
    font-size: 0.78rem;
    left: 0;
    position: absolute;
    right: 0;
  }

  .hour-row span {
    background: #fff;
    display: inline-block;
    padding: 0.1rem 0.4rem;
  }

  .scheduled-block {
    background: #e8f2ff;
    border: 1px solid #6aa6f8;
    border-left: 5px solid var(--task-color);
    border-radius: 6px;
    box-sizing: border-box;
    cursor: grab;
    display: grid;
    gap: 0.35rem;
    grid-template-columns: minmax(0, 1fr) auto auto;
    left: 4.8rem;
    min-height: 52px;
    overflow: hidden;
    padding: 0.45rem;
    position: absolute;
    right: 0.5rem;
  }

  .external-block {
    background: #e8eaed;
    border: 1px solid #aeb4bd;
    border-left: 5px solid #727b86;
    border-radius: 6px;
    box-sizing: border-box;
    color: #333942;
    display: grid;
    gap: 0.1rem;
    grid-template-columns: minmax(0, 1fr) auto;
    left: 4.8rem;
    min-height: 32px;
    opacity: 0.9;
    overflow: hidden;
    padding: 0.4rem;
    position: absolute;
    right: 0.5rem;
    z-index: 1;
  }

  .external-block.non-blocking {
    background: #f5f6f8;
    border-style: dashed;
    opacity: 0.72;
  }

  .external-block span {
    color: #59616d;
    font-size: 0.8rem;
  }

  .external-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    justify-content: flex-end;
  }

  .external-controls input {
    max-width: 120px;
    padding: 0.25rem 0.35rem;
  }

  .external-controls button {
    font-size: 0.78rem;
    padding: 0.25rem 0.4rem;
  }

  .scheduled-block {
    z-index: 2;
  }

  .scheduled-block.done {
    background: #edf8ee;
    border-color: #79bd84;
  }

  .block-copy {
    display: grid;
    gap: 0.15rem;
    min-width: 0;
  }

  .block-copy strong {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .manual-time,
  .block-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    justify-content: flex-end;
  }

  .manual-time input {
    max-width: 74px;
    padding: 0.25rem 0.35rem;
  }

  .manual-time button,
  .block-actions button {
    font-size: 0.78rem;
    padding: 0.25rem 0.4rem;
  }

  .status,
  .empty {
    color: #596679;
  }

  .error {
    background: #fff0f0;
    border: 1px solid #e7a7a7;
    border-radius: 6px;
    color: #9d2525;
    padding: 0.7rem;
  }

  @media (max-width: 980px) {
    .app-shell {
      grid-template-columns: 1fr;
    }

    .scheduled-block {
      grid-template-columns: 1fr;
      left: 4.4rem;
    }

    .manual-time,
    .block-actions {
      justify-content: flex-start;
    }
  }
</style>
