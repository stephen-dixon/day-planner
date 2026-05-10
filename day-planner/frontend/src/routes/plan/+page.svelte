<script lang="ts">
  import { onMount } from 'svelte';
  import TaskDetail from '$lib/TaskDetail.svelte';
  import { completeTask, createDayBlock, createTask, deleteDayBlock, getDayBlocks, getTasks, updateDayBlock, updateTask } from '$lib/api';
  import { minutesToTimeLabel, snapToIncrement, todayISODate } from '$lib/time';
  import type { DayBlock, Task } from '$lib/types';

  const dayStart = 7 * 60;
  const dayEnd = 22 * 60;
  const timelineHeight = 900;
  const pixelsPerMinute = timelineHeight / (dayEnd - dayStart);

  let selectedDate = todayISODate();
  let tasks: Task[] = [];
  let blocks: DayBlock[] = [];
  let selectedTask: Task | null = null;
  let loading = true;
  let saving = false;
  let error = '';
  let newTitle = '';
  let newEstimate = 45;

  $: activeTasks = tasks.filter((task) => task.status !== 'done' && task.status !== 'archived');
  $: hours = Array.from({ length: 16 }, (_, index) => dayStart + index * 60);

  function taskForBlock(block: DayBlock): Task | undefined {
    return block.task_id ? tasks.find((task) => task.id === block.task_id) : undefined;
  }

  function sourceLabel(task: Task): string {
    return task.source_label || task.source_type[0].toUpperCase() + task.source_type.slice(1);
  }

  function progressLabel(task: Task): string {
    const clarity = task.clarity_progress === null ? '' : ` · clarity ${task.clarity_progress}%`;
    return `${task.task_phase}${clarity}`;
  }

  function blockTop(block: DayBlock): number {
    return (block.start_minute - dayStart) * pixelsPerMinute;
  }

  function blockHeight(block: DayBlock): number {
    return Math.max(22, (block.end_minute - block.start_minute) * pixelsPerMinute);
  }

  function dragTask(event: DragEvent, task: Task): void {
    event.dataTransfer?.setData('application/day-planner-task-id', String(task.id));
  }

  function dragBlock(event: DragEvent, block: DayBlock): void {
    event.dataTransfer?.setData('application/day-planner-block-id', String(block.id));
  }

  function minuteFromDrop(event: DragEvent, duration: number): number {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const raw = dayStart + ((event.clientY - rect.top) / pixelsPerMinute);
    return Math.min(Math.max(snapToIncrement(raw), dayStart), dayEnd - duration);
  }

  async function refresh(): Promise<void> {
    [tasks, blocks] = await Promise.all([getTasks(), getDayBlocks(selectedDate)]);
    if (selectedTask) selectedTask = tasks.find((task) => task.id === selectedTask?.id) ?? null;
  }

  async function load(): Promise<void> {
    loading = true;
    error = '';
    try {
      await refresh();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load planner.';
    } finally {
      loading = false;
    }
  }

  async function addTask(): Promise<void> {
    if (!newTitle.trim()) return;
    saving = true;
    error = '';
    try {
      await createTask({ title: newTitle.trim(), estimated_minutes: newEstimate || null });
      newTitle = '';
      newEstimate = 45;
      await refresh();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not create task.';
    } finally {
      saving = false;
    }
  }

  async function dropOnTimeline(event: DragEvent): Promise<void> {
    event.preventDefault();
    const taskId = event.dataTransfer?.getData('application/day-planner-task-id');
    const blockId = event.dataTransfer?.getData('application/day-planner-block-id');
    saving = true;
    error = '';
    try {
      if (taskId) {
        const task = tasks.find((item) => item.id === Number(taskId));
        if (!task) return;
        const duration = task.estimated_minutes ?? 45;
        const start = minuteFromDrop(event, duration);
        await createDayBlock(selectedDate, {
          task_id: task.id,
          start_minute: start,
          end_minute: start + duration,
          block_type: 'task',
          commitment_strength: 'soft'
        });
        await updateTask(task.id, { planned_date: selectedDate });
      } else if (blockId) {
        const block = blocks.find((item) => item.id === Number(blockId));
        if (!block) return;
        const duration = block.end_minute - block.start_minute;
        const start = minuteFromDrop(event, duration);
        await updateDayBlock(block.id, { start_minute: start, end_minute: start + duration });
      }
      await refresh();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not update plan.';
    } finally {
      saving = false;
    }
  }

  async function markDone(block: DayBlock): Promise<void> {
    await updateDayBlock(block.id, { status: 'done' });
    if (block.task_id) await completeTask(block.task_id, { completed_on: block.date, source_block_id: block.id });
    await refresh();
  }

  async function removeBlock(block: DayBlock): Promise<void> {
    await deleteDayBlock(block.id);
    await refresh();
  }

  onMount(load);
</script>

<svelte:head><title>Plan Day</title></svelte:head>

<main class="shell">
  <section class="panel backlog">
    <div class="header">
      <div>
        <p class="eyebrow">Plan Day</p>
        <h1>Backlog</h1>
      </div>
      <a href="/support">Support Mode</a>
    </div>
    <form class="quick-add" on:submit|preventDefault={addTask}>
      <input bind:value={newTitle} placeholder="Add local task" />
      <input bind:value={newEstimate} min="5" step="5" type="number" aria-label="Estimate minutes" />
      <button disabled={saving || !newTitle.trim()} type="submit">Add</button>
    </form>
    {#each activeTasks as task}
      <article class="task-card" draggable="true" on:dragstart={(event) => dragTask(event, task)}>
        <div>
          <strong>{task.title}</strong>
          <span>{sourceLabel(task)} · {task.estimated_minutes ?? 45} min · {progressLabel(task)}</span>
        </div>
        <button type="button" on:click={() => (selectedTask = task)}>Details</button>
      </article>
    {/each}
  </section>

  <section class="panel planner">
    <div class="header">
      <div>
        <p class="eyebrow">Timeline</p>
        <h2>{selectedDate}</h2>
      </div>
      <input bind:value={selectedDate} type="date" on:change={load} />
    </div>
    {#if loading}<p>Loading...</p>{/if}
    {#if saving}<p>Saving...</p>{/if}
    {#if error}<p class="error">{error}</p>{/if}
    <div class="timeline" role="application" aria-label="Day timeline drop area" style={`height: ${timelineHeight}px;`} on:dragover|preventDefault on:drop={dropOnTimeline}>
      {#each hours as hour}
        <div class="hour" style={`top: ${(hour - dayStart) * pixelsPerMinute}px;`}><span>{minutesToTimeLabel(hour)}</span></div>
      {/each}
      {#each blocks as block}
        {@const task = taskForBlock(block)}
        <article class:done={block.status === 'done'} class="block" draggable="true" style={`top: ${blockTop(block)}px; height: ${blockHeight(block)}px;`} on:dragstart={(event) => dragBlock(event, block)}>
          <div>
            <strong>{block.title_override || task?.title || block.block_type}</strong>
            <span>{minutesToTimeLabel(block.start_minute)}-{minutesToTimeLabel(block.end_minute)} · {block.commitment_strength}</span>
          </div>
          <button type="button" on:click={() => task && (selectedTask = task)}>Details</button>
          <button type="button" on:click={() => markDone(block)}>Done</button>
          <button type="button" on:click={() => removeBlock(block)}>Remove</button>
        </article>
      {/each}
    </div>
  </section>

  {#if selectedTask}
    <TaskDetail task={selectedTask} on:saved={refresh} on:close={() => (selectedTask = null)} />
  {/if}
</main>

<style>
  .shell {
    display: grid;
    gap: 1rem;
    grid-template-columns: 360px minmax(520px, 1fr) 430px;
    margin: 0 auto;
    max-width: 1480px;
    padding: 1rem;
  }

  .panel {
    background: #fff;
    border: 1px solid #d9e0e8;
    border-radius: 10px;
    padding: 1rem;
  }

  .header,
  .task-card,
  .block {
    align-items: center;
    display: flex;
    gap: 0.75rem;
    justify-content: space-between;
  }

  h1,
  h2,
  p {
    margin: 0;
  }

  .eyebrow,
  span {
    color: #657186;
    font-size: 0.82rem;
  }

  .quick-add {
    display: grid;
    gap: 0.5rem;
    grid-template-columns: 1fr 80px auto;
    margin: 1rem 0;
  }

  .task-card {
    border: 1px solid #d9e0e8;
    border-left: 5px solid #2f80ed;
    border-radius: 8px;
    cursor: grab;
    margin-bottom: 0.65rem;
    padding: 0.75rem;
  }

  .task-card div,
  .block div {
    display: grid;
    gap: 0.2rem;
  }

  .timeline {
    background: linear-gradient(#eef3f7 1px, transparent 1px) 0 0 / 100% 60px, #fbfcfe;
    border: 1px solid #d9e0e8;
    border-radius: 10px;
    margin-top: 1rem;
    position: relative;
  }

  .hour {
    border-top: 1px solid #e7edf3;
    left: 0;
    position: absolute;
    right: 0;
  }

  .hour span {
    background: #fbfcfe;
    padding: 0 0.4rem;
  }

  .block {
    background: #e8f2ff;
    border: 1px solid #9ec5fe;
    border-left: 5px solid #1d5fb8;
    border-radius: 8px;
    left: 72px;
    min-height: 22px;
    padding: 0.45rem;
    position: absolute;
    right: 12px;
  }

  .block.done {
    opacity: 0.58;
  }

  .error {
    color: #b42318;
  }

  @media (max-width: 1100px) {
    .shell {
      grid-template-columns: 1fr;
    }
  }
</style>
