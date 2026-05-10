<script lang="ts">
  import { onMount } from 'svelte';
  import TaskDetail from '$lib/TaskDetail.svelte';
  import { aiPlanDay, aiReflectSession, createDayBlock, getAIStatus, getTasks, recommendTasks } from '$lib/api';
  import { todayISODate } from '$lib/time';
  import type { AIStatus, EnergyLevel, FocusState, PlannedDayProposal, SessionReflection, SuggestedBlock, Task, TaskContext, TaskRecommendation } from '$lib/types';

  const contexts: TaskContext[] = ['unknown', 'coding', 'writing', 'admin', 'household', 'errands', 'social', 'research', 'planning', 'other'];

  let tasks: Task[] = [];
  let recommendations: TaskRecommendation[] = [];
  let selectedTask: Task | null = null;
  let energy: EnergyLevel = 'medium';
  let focus: FocusState = 'okay';
  let availableMinutes = 45;
  let preferredContext: TaskContext = 'unknown';
  let scheduleDate = todayISODate();
  let scheduleStart = 9 * 60;
  let aiStatus: AIStatus | null = null;
  let dayIntentions = '';
  let dayProposal: PlannedDayProposal | null = null;
  let editableBlocks: SuggestedBlock[] = [];
  let reflectionTaskId = '';
  let reflectionOutcome = 'partial';
  let reflectionNote = '';
  let reflection: SessionReflection | null = null;
  let loading = true;
  let saving = false;
  let error = '';

  async function load(): Promise<void> {
    loading = true;
    error = '';
    try {
      [tasks, aiStatus] = await Promise.all([getTasks(), getAIStatus()]);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load tasks.';
    } finally {
      loading = false;
    }
  }

  async function planMyDay(): Promise<void> {
    saving = true;
    error = '';
    try {
      dayProposal = await aiPlanDay({
        date: scheduleDate,
        energy,
        focus,
        available_minutes: availableMinutes || null,
        free_text: dayIntentions.trim() || null,
        preferred_context: preferredContext === 'unknown' ? null : preferredContext
      });
      editableBlocks = dayProposal.suggested_blocks.map((block) => ({ ...block }));
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not plan day with AI.';
    } finally {
      saving = false;
    }
  }

  async function applyProposedBlock(block: SuggestedBlock): Promise<void> {
    await createDayBlock(scheduleDate, {
      task_id: block.task_id,
      task_step_id: block.task_step_id,
      title_override: block.title,
      start_minute: block.start_minute,
      end_minute: block.end_minute,
      block_type: block.task_step_id ? 'step' : block.task_id ? 'task' : 'other',
      commitment_strength: 'soft'
    });
  }

  async function applyAllBlocks(): Promise<void> {
    for (const block of editableBlocks) {
      await applyProposedBlock(block);
    }
  }

  async function reflectOnSession(): Promise<void> {
    if (!reflectionTaskId || !reflectionNote.trim()) return;
    saving = true;
    error = '';
    try {
      reflection = await aiReflectSession({
        task_id: Number(reflectionTaskId),
        session_note: reflectionNote.trim(),
        outcome: reflectionOutcome
      });
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not reflect on session.';
    } finally {
      saving = false;
    }
  }

  async function suggest(): Promise<void> {
    saving = true;
    error = '';
    try {
      recommendations = await recommendTasks({
        energy,
        focus,
        available_minutes: availableMinutes || null,
        preferred_context: preferredContext === 'unknown' ? null : preferredContext
      });
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not suggest tasks.';
    } finally {
      saving = false;
    }
  }

  async function scheduleTask(task: Task): Promise<void> {
    const duration = task.estimated_minutes ?? availableMinutes ?? 45;
    await createDayBlock(scheduleDate, {
      task_id: task.id,
      start_minute: scheduleStart,
      end_minute: scheduleStart + duration,
      block_type: 'task',
      commitment_strength: 'soft'
    });
  }

  async function scheduleStarter(task: Task): Promise<void> {
    await createDayBlock(scheduleDate, {
      task_id: task.id,
      start_minute: scheduleStart,
      end_minute: scheduleStart + Math.min(availableMinutes || 15, 25),
      block_type: 'task',
      title_override: task.starter_step || `Starter: ${task.title}`,
      commitment_strength: 'optional'
    });
  }

  function sourceLabel(task: Task): string {
    return task.source_label || task.source_type[0].toUpperCase() + task.source_type.slice(1);
  }

  function progress(task: Task): string {
    return task.clarity_progress === null ? task.task_phase : `${task.task_phase} · clarity ${task.clarity_progress}%`;
  }

  onMount(load);
</script>

<svelte:head><title>Support Mode</title></svelte:head>

<main class="shell">
  <section class="panel controls">
    <div class="header">
      <div>
        <p class="eyebrow">Support Mode</p>
        <h1>Find realistic work</h1>
      </div>
      <a href="/plan">Plan Day</a>
    </div>
    <div class="state-grid">
      <label>Energy<select bind:value={energy}><option>low</option><option>medium</option><option>high</option></select></label>
      <label>Focus<select bind:value={focus}><option>scattered</option><option>okay</option><option>deep</option></select></label>
      <label>Available minutes<input min="5" step="5" type="number" bind:value={availableMinutes} /></label>
      <label>Preferred context<select bind:value={preferredContext}>{#each contexts as context}<option value={context}>{context}</option>{/each}</select></label>
      <label>Schedule date<input type="date" bind:value={scheduleDate} /></label>
      <label>Start minute<input min="0" max="1439" step="15" type="number" bind:value={scheduleStart} /></label>
    </div>
    <button type="button" on:click={suggest} disabled={saving}>Suggest realistic tasks</button>
    <div class="ai-tools">
      <p>{aiStatus?.configured ? `AI: ${aiStatus.provider} · ${aiStatus.model}` : aiStatus?.message || 'AI status unavailable.'}</p>
      <label>Intentions<textarea rows="4" bind:value={dayIntentions} placeholder="I want to make progress on the presentation, but activation feels hard today."></textarea></label>
      <button type="button" on:click={planMyDay} disabled={saving || !aiStatus?.configured}>Plan my day</button>
      <form class="reflect" on:submit|preventDefault={reflectOnSession}>
        <label>Reflect task<select bind:value={reflectionTaskId}><option value="">Choose task</option>{#each tasks as task}<option value={task.id}>{task.title}</option>{/each}</select></label>
        <label>Outcome<select bind:value={reflectionOutcome}><option>partial</option><option>completed</option><option>abandoned</option><option>unknown</option></select></label>
        <label>Session note<textarea rows="3" bind:value={reflectionNote} placeholder="I opened the report but realised I don’t know the narrative."></textarea></label>
        <button type="submit" disabled={saving || !aiStatus?.configured || !reflectionTaskId || !reflectionNote.trim()}>Reflect on session</button>
      </form>
    </div>
    {#if loading}<p>Loading...</p>{/if}
    {#if saving}<p>Working...</p>{/if}
    {#if error}<p class="error">{error}</p>{/if}
  </section>

  <section class="panel suggestions">
    <div class="header">
      <div>
        <p class="eyebrow">Ranked suggestions</p>
        <h2>{recommendations.length || tasks.length} candidates</h2>
      </div>
    </div>
    {#each (recommendations.length ? recommendations : tasks.map((task) => ({ task, score: 0, reasons: ['not ranked yet'] }))) as item}
      <article class="suggestion">
        <div class="score">Score {item.score}</div>
        <div class="copy">
          <strong>{item.task.title}</strong>
          <span>{sourceLabel(item.task)} · {progress(item.task)}</span>
          <p>{item.task.starter_step || 'No starter step set yet.'}</p>
          <div class="chips">
            <small>activation {item.task.activation_cost}</small>
            <small>energy {item.task.energy_required}</small>
            <small>focus {item.task.focus_required}</small>
            <small>momentum {item.task.momentum_state}</small>
          </div>
          <span>{item.reasons.join(' · ')}</span>
        </div>
        <div class="actions">
          <button type="button" on:click={() => scheduleTask(item.task)}>Schedule task</button>
          <button type="button" on:click={() => scheduleStarter(item.task)} disabled={!item.task.starter_step}>Schedule starter step</button>
          <button type="button" on:click={() => (selectedTask = item.task)}>Open details</button>
          <button type="button" on:click={() => (selectedTask = item.task)}>AI enrich</button>
          <button type="button" on:click={() => (selectedTask = item.task)}>Break down</button>
        </div>
      </article>
    {/each}
  </section>

  {#if dayProposal || reflection}
    <section class="panel ai-output">
      {#if dayProposal}
        <div class="header">
          <div>
            <p class="eyebrow">Plan My Day proposal</p>
            <h2>{dayProposal.summary}</h2>
          </div>
          <button type="button" on:click={applyAllBlocks}>Accept all</button>
        </div>
        {#if dayProposal.warnings.length}
          <div class="warning">{dayProposal.warnings.join(' ')}</div>
        {/if}
        <p>{dayProposal.rationale}</p>
        {#each editableBlocks as block}
          <article class="block-proposal">
            <input bind:value={block.title} aria-label="Block title" />
            <input bind:value={block.start_minute} type="number" min="0" max="1439" step="15" aria-label="Start minute" />
            <input bind:value={block.end_minute} type="number" min="1" max="1440" step="15" aria-label="End minute" />
            <span>{block.reasoning}</span>
            <button type="button" on:click={() => applyProposedBlock(block)}>Accept block</button>
          </article>
        {/each}
      {/if}
      {#if reflection}
        <article class="reflection">
          <p class="eyebrow">Session reflection proposal</p>
          <strong>{reflection.suggested_next_action}</strong>
          <span>Friction: {reflection.inferred_friction_reason || 'unclear'} · phase: {reflection.suggested_task_phase}</span>
          <p>{reflection.reasoning || 'No reasoning supplied.'}</p>
        </article>
      {/if}
    </section>
  {/if}

  {#if selectedTask}
    <TaskDetail task={selectedTask} on:saved={load} on:close={() => (selectedTask = null)} />
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

  .header {
    align-items: start;
    display: flex;
    gap: 1rem;
    justify-content: space-between;
    margin-bottom: 1rem;
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

  .state-grid {
    display: grid;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .ai-tools,
  .reflect,
  .ai-output {
    display: grid;
    gap: 0.75rem;
  }

  label {
    color: #4f5d6f;
    display: grid;
    font-size: 0.86rem;
    gap: 0.3rem;
  }

  .suggestion {
    border: 1px solid #d9e0e8;
    border-radius: 10px;
    display: grid;
    gap: 0.75rem;
    grid-template-columns: 82px 1fr auto;
    margin-bottom: 0.75rem;
    padding: 0.85rem;
  }

  .score {
    color: #1d5fb8;
    font-weight: 700;
  }

  .copy {
    display: grid;
    gap: 0.35rem;
  }

  .copy p {
    background: #f6f8fb;
    border-radius: 8px;
    padding: 0.55rem;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }

  .chips small {
    background: #e8f2ff;
    border-radius: 999px;
    padding: 0.18rem 0.5rem;
  }

  .actions {
    display: grid;
    gap: 0.4rem;
  }

  .block-proposal {
    border: 1px solid #d9e0e8;
    border-radius: 10px;
    display: grid;
    gap: 0.5rem;
    grid-template-columns: minmax(160px, 1fr) 90px 90px minmax(180px, 1fr) auto;
    margin-bottom: 0.65rem;
    padding: 0.65rem;
  }

  .warning {
    background: #fff7ed;
    border: 1px solid #fdba74;
    border-radius: 8px;
    padding: 0.65rem;
  }

  .reflection {
    border-top: 1px solid #d9e0e8;
    display: grid;
    gap: 0.35rem;
    margin-top: 1rem;
    padding-top: 1rem;
  }

  .error {
    color: #b42318;
  }

  @media (max-width: 1100px) {
    .shell {
      grid-template-columns: 1fr;
    }

    .suggestion {
      grid-template-columns: 1fr;
    }
  }
</style>
