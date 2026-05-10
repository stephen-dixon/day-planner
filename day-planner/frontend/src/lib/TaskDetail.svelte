<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { aiBreakDownTask, aiEnrichTask, createTaskStep, deleteTaskStep, getAIStatus, getTaskAnalytics, getTaskSteps, updateTask, updateTaskStep } from '$lib/api';
  import type { EnergyLevel, FocusRequired, MomentumState, Task, TaskAnalytics, TaskBreakdown, TaskContext, TaskEnrichment, TaskPhase, TaskStep } from '$lib/types';

  export let task: Task;

  const dispatch = createEventDispatcher<{ saved: Task; close: void }>();
  const energyOptions: EnergyLevel[] = ['unknown', 'low', 'medium', 'high'];
  const focusOptions: FocusRequired[] = ['unknown', 'shallow', 'medium', 'deep'];
  const contextOptions: TaskContext[] = ['unknown', 'coding', 'writing', 'admin', 'household', 'errands', 'social', 'research', 'planning', 'other'];
  const phaseOptions: TaskPhase[] = ['vague', 'clarifying', 'decomposing', 'executable', 'executing', 'refining', 'blocked', 'done'];
  const momentumOptions: MomentumState[] = ['unknown', 'stalled', 'warming_up', 'engaged', 'flowing', 'finishing'];

  let draft = toDraft(task);
  let steps: TaskStep[] = [];
  let analytics: TaskAnalytics | null = null;
  let enrichment: TaskEnrichment | null = null;
  let breakdown: TaskBreakdown | null = null;
  let aiConfigured = false;
  let aiMessage = 'Checking AI configuration...';
  let newStepTitle = '';
  let saving = false;
  let error = '';

  $: if (task.id !== draft.id) {
    draft = toDraft(task);
    loadSteps();
  }
  $: doneSteps = steps.filter((step) => step.status === 'done').length;

  function toDraft(item: Task) {
    return {
      id: item.id,
      title: item.title,
      notes: item.notes ?? '',
      estimated_minutes: item.estimated_minutes ?? 60,
      deadline: item.deadline ?? '',
      energy_required: item.energy_required,
      activation_cost: item.activation_cost,
      focus_required: item.focus_required,
      interest_level: item.interest_level,
      context: item.context,
      task_phase: item.task_phase,
      clarity_progress: item.clarity_progress ?? 0,
      momentum_state: item.momentum_state,
      starter_step: item.starter_step ?? '',
      friction_notes: item.friction_notes ?? ''
    };
  }

  async function loadSteps(): Promise<void> {
    error = '';
    try {
      steps = await getTaskSteps(task.id);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load steps.';
    }
  }

  async function loadAnalytics(): Promise<void> {
    try {
      analytics = await getTaskAnalytics(task.id);
    } catch {
      analytics = null;
    }
  }

  async function loadAIStatus(): Promise<void> {
    try {
      const status = await getAIStatus();
      aiConfigured = status.configured;
      aiMessage = status.configured ? `${status.provider} · ${status.model}` : status.message || 'AI is not configured.';
    } catch {
      aiConfigured = false;
      aiMessage = 'AI status unavailable.';
    }
  }

  async function saveTask(): Promise<void> {
    saving = true;
    error = '';
    try {
      const saved = await updateTask(task.id, {
        title: draft.title.trim(),
        notes: draft.notes.trim() || null,
        estimated_minutes: draft.estimated_minutes || null,
        deadline: draft.deadline || null,
        energy_required: draft.energy_required,
        activation_cost: draft.activation_cost,
        focus_required: draft.focus_required,
        interest_level: draft.interest_level,
        context: draft.context,
        task_phase: draft.task_phase,
        clarity_progress: draft.clarity_progress,
        momentum_state: draft.momentum_state,
        starter_step: draft.starter_step.trim() || null,
        friction_notes: draft.friction_notes.trim() || null
      });
      dispatch('saved', saved);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not save task.';
    } finally {
      saving = false;
    }
  }

  async function addStep(): Promise<void> {
    if (!newStepTitle.trim()) return;
    saving = true;
    error = '';
    try {
      await createTaskStep(task.id, { title: newStepTitle.trim() });
      newStepTitle = '';
      await loadSteps();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not add step.';
    } finally {
      saving = false;
    }
  }

  async function requestEnrichment(): Promise<void> {
    saving = true;
    error = '';
    try {
      enrichment = await aiEnrichTask(task.id);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not get AI enrichment.';
    } finally {
      saving = false;
    }
  }

  function acceptEnrichment(): void {
    if (!enrichment) return;
    draft.energy_required = enrichment.suggested_energy_required;
    draft.activation_cost = enrichment.suggested_activation_cost;
    draft.focus_required = enrichment.suggested_focus_required;
    draft.interest_level = enrichment.suggested_interest_level;
    draft.context = enrichment.suggested_context;
    draft.task_phase = enrichment.suggested_task_phase;
    draft.starter_step = enrichment.suggested_starter_step ?? draft.starter_step;
  }

  async function requestBreakdown(): Promise<void> {
    saving = true;
    error = '';
    try {
      breakdown = await aiBreakDownTask(task.id);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not get AI breakdown.';
    } finally {
      saving = false;
    }
  }

  async function acceptBreakdown(): Promise<void> {
    if (!breakdown) return;
    draft.starter_step = breakdown.starter_step;
    for (const title of breakdown.suggested_steps) {
      await createTaskStep(task.id, { title });
    }
    await loadSteps();
  }

  async function setStepStatus(step: TaskStep, status: 'todo' | 'done' | 'skipped'): Promise<void> {
    await updateTaskStep(step.id, { status });
    await loadSteps();
  }

  async function moveStep(step: TaskStep, delta: number): Promise<void> {
    const ordered = [...steps].sort((a, b) => a.order_index - b.order_index || a.id - b.id);
    const index = ordered.findIndex((item) => item.id === step.id);
    const swap = ordered[index + delta];
    if (!swap) return;
    await Promise.all([
      updateTaskStep(step.id, { order_index: swap.order_index }),
      updateTaskStep(swap.id, { order_index: step.order_index })
    ]);
    await loadSteps();
  }

  async function removeStep(step: TaskStep): Promise<void> {
    await deleteTaskStep(step.id);
    await loadSteps();
  }

  onMount(() => {
    loadSteps();
    loadAnalytics();
    loadAIStatus();
  });
</script>

<aside class="detail-panel">
  <div class="header">
    <div>
      <p class="eyebrow">Task details</p>
      <h2>{task.title}</h2>
      <p class="source">{task.source_label || task.source_type}</p>
    </div>
    <button type="button" on:click={() => dispatch('close')}>Close</button>
  </div>

  {#if error}<p class="error">{error}</p>{/if}

  <section class="ai-box">
    <div class="header compact">
      <h3>AI proposals</h3>
      <span>{aiMessage}. Suggestions only. Review before saving.</span>
    </div>
    <div class="button-row">
      <button type="button" on:click={requestEnrichment} disabled={saving || !aiConfigured}>AI enrich</button>
      <button type="button" on:click={requestBreakdown} disabled={saving || !aiConfigured}>Break down</button>
    </div>
    {#if enrichment}
      <article class="proposal">
        <strong>Enrichment proposal</strong>
        <span>{enrichment.reasoning || 'No reasoning supplied.'}</span>
        <div class="chips">
          <small>energy {enrichment.suggested_energy_required}</small>
          <small>activation {enrichment.suggested_activation_cost}</small>
          <small>focus {enrichment.suggested_focus_required}</small>
          <small>context {enrichment.suggested_context}</small>
          <small>phase {enrichment.suggested_task_phase}</small>
        </div>
        {#if enrichment.suggested_starter_step}<p>{enrichment.suggested_starter_step}</p>{/if}
        <button type="button" on:click={acceptEnrichment}>Accept into editor</button>
      </article>
    {/if}
    {#if breakdown}
      <article class="proposal">
        <strong>Breakdown proposal</strong>
        <span>{breakdown.reasoning || 'No reasoning supplied.'}</span>
        <p>{breakdown.starter_step}</p>
        <ol>
          {#each breakdown.suggested_steps as step}
            <li>{step}</li>
          {/each}
        </ol>
        <button type="button" on:click={acceptBreakdown}>Add proposed steps</button>
      </article>
    {/if}
  </section>

  {#if analytics}
    <section class="analytics-box">
      <div class="header compact">
        <h3>Analytics</h3>
        <span>Confidence: {analytics.confidence_level}</span>
      </div>
      <p>{analytics.duration_summary}</p>
      <p>{analytics.activation_risk}</p>
      <dl>
        <div><dt>Avg actual</dt><dd>{analytics.average_actual_minutes ?? 'No actuals yet'}</dd></div>
        <div><dt>Estimate ratio</dt><dd>{analytics.estimate_ratio ?? 'No pattern yet'}</dd></div>
        <div><dt>Sessions</dt><dd>{analytics.average_sessions_to_completion ? `Typically ${analytics.average_sessions_to_completion} sessions` : 'No completion pattern yet'}</dd></div>
        <div><dt>Skipped blocks</dt><dd>{analytics.reschedule_count}</dd></div>
      </dl>
      {#if analytics.common_friction_reasons.length}
        <p>Common friction: {analytics.common_friction_reasons.join(', ')}</p>
      {/if}
      {#if analytics.timing_patterns.length}
        <p>{analytics.timing_patterns.join(' ')}</p>
      {/if}
      <span>Signals used: {analytics.signals_used.join(', ')}</span>
    </section>
  {/if}

  <form class="editor" on:submit|preventDefault={saveTask}>
    <label>Title<input bind:value={draft.title} /></label>
    <label>Notes<textarea rows="4" bind:value={draft.notes}></textarea></label>
    <div class="grid">
      <label>Estimate<input min="1" type="number" bind:value={draft.estimated_minutes} /></label>
      <label>Deadline<input type="date" bind:value={draft.deadline} /></label>
      <label>Energy<select bind:value={draft.energy_required}>{#each energyOptions as option}<option value={option}>{option}</option>{/each}</select></label>
      <label>Activation<select bind:value={draft.activation_cost}>{#each energyOptions as option}<option value={option}>{option}</option>{/each}</select></label>
      <label>Focus<select bind:value={draft.focus_required}>{#each focusOptions as option}<option value={option}>{option}</option>{/each}</select></label>
      <label>Interest<select bind:value={draft.interest_level}>{#each energyOptions as option}<option value={option}>{option}</option>{/each}</select></label>
      <label>Context<select bind:value={draft.context}>{#each contextOptions as option}<option value={option}>{option}</option>{/each}</select></label>
      <label>Phase<select bind:value={draft.task_phase}>{#each phaseOptions as option}<option value={option}>{option}</option>{/each}</select></label>
      <label>Clarity %<input min="0" max="100" type="number" bind:value={draft.clarity_progress} /></label>
      <label>Momentum<select bind:value={draft.momentum_state}>{#each momentumOptions as option}<option value={option}>{option}</option>{/each}</select></label>
    </div>
    <label>Starter step<textarea rows="2" bind:value={draft.starter_step}></textarea></label>
    <label>Friction notes<textarea rows="2" bind:value={draft.friction_notes}></textarea></label>
    <div class="source-box">
      <span>Source fields are read-only for now.</span>
      <code>{task.source_type}</code>
      <code>{task.source_id ?? 'no source id'}</code>
      {#if task.source_url}<a href={task.source_url} target="_blank" rel="noreferrer">Open source</a>{/if}
    </div>
    <button type="submit" disabled={saving || !draft.title.trim()}>Save task</button>
  </form>

  <section class="steps">
    <div class="header compact">
      <h3>Steps</h3>
      <span>{steps.length ? `${doneSteps}/${steps.length} steps done` : 'No steps yet'}</span>
    </div>
    <form class="step-create" on:submit|preventDefault={addStep}>
      <input bind:value={newStepTitle} placeholder="Small next action" />
      <button type="submit" disabled={!newStepTitle.trim() || saving}>Add step</button>
    </form>
    {#each steps as step}
      <article class:done={step.status === 'done'} class="step-row">
        <div>
          <strong>{step.title}</strong>
          <span>{step.status} · activation {step.activation_cost}</span>
        </div>
        <button type="button" on:click={() => moveStep(step, -1)}>Up</button>
        <button type="button" on:click={() => moveStep(step, 1)}>Down</button>
        <button type="button" on:click={() => setStepStatus(step, step.status === 'done' ? 'todo' : 'done')}>{step.status === 'done' ? 'Undo' : 'Done'}</button>
        <button type="button" on:click={() => removeStep(step)}>Delete</button>
      </article>
    {/each}
  </section>
</aside>

<style>
  .detail-panel {
    background: #fff;
    border: 1px solid #d9e0e8;
    border-radius: 10px;
    padding: 1rem;
  }

  .header {
    align-items: start;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
  }

  .compact {
    align-items: center;
  }

  h2,
  h3,
  p {
    margin: 0;
  }

  .eyebrow,
  .source,
  .step-row span {
    color: #657186;
    font-size: 0.82rem;
  }

  .editor,
  .steps {
    display: grid;
    gap: 0.75rem;
    margin-top: 1rem;
  }

  label {
    color: #4f5d6f;
    display: grid;
    font-size: 0.86rem;
    gap: 0.3rem;
  }

  .grid {
    display: grid;
    gap: 0.6rem;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .source-box,
  .ai-box,
  .analytics-box,
  .proposal,
  .step-row {
    align-items: center;
    border: 1px solid #edf1f5;
    border-radius: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.65rem;
  }

  .source-box code {
    background: #f1f5f9;
    border-radius: 5px;
    padding: 0.2rem 0.4rem;
  }

  .ai-box,
  .analytics-box,
  .proposal {
    align-items: stretch;
    display: grid;
    margin-top: 1rem;
  }

  .button-row,
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }

  .chips small {
    background: #e8f2ff;
    border-radius: 999px;
    padding: 0.18rem 0.5rem;
  }

  dl {
    display: grid;
    gap: 0.35rem;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    margin: 0;
  }

  dt {
    color: #657186;
    font-size: 0.78rem;
  }

  dd {
    margin: 0;
  }

  .step-create {
    display: grid;
    gap: 0.5rem;
    grid-template-columns: 1fr auto;
  }

  .step-row {
    justify-content: end;
  }

  .step-row div {
    display: grid;
    gap: 0.15rem;
    margin-right: auto;
  }

  .step-row.done strong {
    text-decoration: line-through;
  }

  .error {
    color: #b42318;
    margin-top: 0.75rem;
  }
</style>
