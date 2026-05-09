<script lang="ts">
  import { onMount } from 'svelte';
  import { getHabitStats } from '$lib/api';
  import type { HabitStats } from '$lib/types';

  let timeframe = 30;
  let stats: HabitStats[] = [];
  let loading = true;
  let error = '';

  type HabitPeriod = {
    label: string;
    title: string;
    complete: boolean;
  };

  function statusLabel(status: string): string {
    if (status === 'on_track') return 'On track';
    if (status === 'behind') return 'Behind';
    return 'Ahead';
  }

  function completionDates(item: HabitStats): string {
    return item.completions.map((completion) => completion.completed_on).join(', ') || 'No completions logged';
  }

  function parseISODate(value: string): Date {
    return new Date(`${value}T00:00:00`);
  }

  function toISODate(value: Date): string {
    return value.toISOString().slice(0, 10);
  }

  function addDays(value: Date, days: number): Date {
    const next = new Date(value);
    next.setDate(next.getDate() + days);
    return next;
  }

  function shortDate(value: Date): string {
    return value.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  }

  function habitPeriods(item: HabitStats): HabitPeriod[] {
    const completionSet = new Set(item.completions.map((completion) => completion.completed_on));
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (timeframe === 7) {
      const start = addDays(today, -6);
      return Array.from({ length: 7 }, (_, index) => {
        const day = addDays(start, index);
        const iso = toISODate(day);
        return {
          label: day.toLocaleDateString(undefined, { weekday: 'short' }).slice(0, 1),
          title: iso,
          complete: completionSet.has(iso)
        };
      });
    }

    const weekCount = timeframe === 30 ? 5 : 13;
    const start = addDays(today, -(weekCount * 7 - 1));
    return Array.from({ length: weekCount }, (_, index) => {
      const weekStart = addDays(start, index * 7);
      const weekEnd = addDays(weekStart, 6);
      const complete = item.completions.some((completion) => {
        const completed = parseISODate(completion.completed_on);
        return completed >= weekStart && completed <= weekEnd;
      });
      return {
        label: `W${index + 1}`,
        title: `${shortDate(weekStart)}-${shortDate(weekEnd)}`,
        complete
      };
    });
  }

  function periodHeading(): string {
    return timeframe === 7 ? 'Daily check-ins' : 'Weekly check-ins';
  }

  async function loadStats(): Promise<void> {
    loading = true;
    error = '';
    try {
      stats = await getHabitStats(timeframe);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load habits.';
    } finally {
      loading = false;
    }
  }

  onMount(loadStats);
</script>

<svelte:head>
  <title>Habits · Day Planner</title>
</svelte:head>

<main class="habits-page">
  <div class="header">
    <div>
      <p class="eyebrow">Habits</p>
      <h1>Habit adherence</h1>
    </div>
    <label>
      Timeframe
      <select bind:value={timeframe} on:change={loadStats}>
        <option value={7}>Week</option>
        <option value={30}>Month</option>
        <option value={90}>3 months</option>
      </select>
    </label>
  </div>

  {#if loading}
    <p class="muted">Loading habits...</p>
  {/if}
  {#if error}
    <p class="error">{error}</p>
  {/if}

  {#if !loading && stats.length === 0}
    <section class="empty">
      <p>No habits yet. Mark a recurring task as a habit from the planner or tasks page.</p>
    </section>
  {/if}

  <section class="habit-grid">
    {#each stats as item}
      <article class={`habit-card ${item.status}`}>
        <div class="habit-header">
          <div>
            <h2>{item.task.title}</h2>
            <p>{item.task.notes || 'No notes'}</p>
          </div>
          <strong>{statusLabel(item.status)}</strong>
        </div>

        <div class="score">
          <span>{item.completion_count}</span>
          <p>
            completions in {item.timeframe_days} days.
            Target: {item.expected_min === item.expected_max ? item.expected_min : `${item.expected_min}-${item.expected_max}`}.
          </p>
        </div>

        <dl>
          <div><dt>Average gap</dt><dd>{item.average_gap_days ?? 'n/a'} days</dd></div>
          <div><dt>Next planned</dt><dd>{item.task.planned_date ?? 'Unscheduled'}</dd></div>
          <div><dt>Frequency</dt><dd>{item.task.recurrence_type ?? 'not set'}</dd></div>
        </dl>

        <div class="completion-visual">
          <span>{periodHeading()}</span>
          <div class="circle-row">
            {#each habitPeriods(item) as period}
              <div class:complete={period.complete} class="completion-circle" title={period.title}>
                {#if period.complete}
                  ✓
                {/if}
                <small>{period.label}</small>
              </div>
            {/each}
          </div>
        </div>

        <div class="dates">
          <span>Logged dates</span>
          <p>{completionDates(item)}</p>
        </div>
      </article>
    {/each}
  </section>
</main>

<style>
  .habits-page {
    display: grid;
    gap: 1rem;
    max-width: 1120px;
    margin: 0 auto;
    padding: 1rem;
  }

  .header {
    align-items: end;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
  }

  .header label {
    color: #4f5d6f;
    display: grid;
    gap: 0.3rem;
    min-width: 180px;
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
  p {
    margin: 0;
  }

  .habit-grid {
    display: grid;
    gap: 1rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  }

  .habit-card,
  .empty {
    background: #fff;
    border: 1px solid #d9e0e8;
    border-left: 5px solid #aebdcb;
    border-radius: 8px;
    display: grid;
    gap: 1rem;
    padding: 1rem;
  }

  .habit-card.on_track {
    border-left-color: #2f8f45;
  }

  .habit-card.behind {
    border-left-color: #b84b4b;
  }

  .habit-card.ahead {
    border-left-color: #9b6b00;
  }

  .habit-header {
    align-items: start;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
  }

  .habit-header p,
  .muted,
  .dates p {
    color: #596679;
  }

  .score {
    align-items: center;
    display: flex;
    gap: 1rem;
  }

  .score span {
    font-size: 2.5rem;
    font-weight: 800;
  }

  dl {
    display: grid;
    gap: 0.4rem;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin: 0;
  }

  dt,
  .completion-visual span,
  .dates span {
    color: #687385;
    font-size: 0.78rem;
  }

  dd {
    margin: 0;
  }

  .completion-visual {
    display: grid;
    gap: 0.5rem;
  }

  .circle-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .completion-circle {
    align-items: center;
    background: #fff;
    border: 2px solid #cbd7e3;
    border-radius: 999px;
    box-sizing: border-box;
    color: #2f8f45;
    display: grid;
    font-size: 1rem;
    font-weight: 800;
    height: 42px;
    justify-items: center;
    line-height: 1;
    padding-top: 0.35rem;
    width: 42px;
  }

  .completion-circle.complete {
    background: #edf8ee;
    border-color: #2f8f45;
  }

  .completion-circle small {
    color: #687385;
    font-size: 0.62rem;
    font-weight: 700;
  }

  .error {
    background: #fff0f0;
    border: 1px solid #e7a7a7;
    border-radius: 6px;
    color: #9d2525;
    padding: 0.7rem;
  }
</style>
