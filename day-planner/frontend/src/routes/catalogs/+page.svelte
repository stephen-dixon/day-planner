<script lang="ts">
  import { onMount } from 'svelte';
  import {
    clearSelectedCatalog,
    createCatalog,
    getCatalogs,
    getSelectedCatalogName,
    loadCatalog,
    setSelectedCatalog
  } from '$lib/api';
  import type { TaskCatalog } from '$lib/types';

  let catalogs: TaskCatalog[] = [];
  let selectedName = 'default';
  let passwordByCatalog: Record<string, string> = {};
  let newCatalogName = '';
  let newCatalogPassword = '';
  let loading = true;
  let saving = false;
  let error = '';
  let message = '';

  async function refresh(): Promise<void> {
    catalogs = await getCatalogs();
    selectedName = getSelectedCatalogName();
  }

  async function load(name: string): Promise<void> {
    saving = true;
    error = '';
    message = '';
    try {
      const session = await loadCatalog({ name, password: passwordByCatalog[name] ?? '' });
      setSelectedCatalog(session);
      selectedName = session.name;
      message = `Loaded ${session.name}. Other pages now use its database.`;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load catalog.';
    } finally {
      saving = false;
    }
  }

  async function create(): Promise<void> {
    if (!newCatalogName.trim() || !newCatalogPassword.trim()) return;
    saving = true;
    error = '';
    message = '';
    try {
      await createCatalog({ name: newCatalogName.trim(), password: newCatalogPassword });
      const session = await loadCatalog({ name: newCatalogName.trim(), password: newCatalogPassword });
      setSelectedCatalog(session);
      newCatalogName = '';
      newCatalogPassword = '';
      message = `Created and loaded ${session.name}.`;
      await refresh();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not create catalog.';
    } finally {
      saving = false;
    }
  }

  function useDefault(): void {
    clearSelectedCatalog();
    selectedName = 'default';
    message = 'Using default planner.db catalog.';
  }

  onMount(async () => {
    try {
      await refresh();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load catalogs.';
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>Catalogs · Day Planner</title>
</svelte:head>

<main class="catalog-page">
  <section class="panel">
    <div>
      <p class="eyebrow">Task catalogs</p>
      <h1>Choose a database</h1>
      <p class="muted">Each catalog is a separate SQLite file, useful for work, home, weekend, or client contexts.</p>
    </div>

    {#if loading}
      <p class="muted">Loading catalogs...</p>
    {/if}
    {#if error}
      <p class="error">{error}</p>
    {/if}
    {#if message}
      <p class="message">{message}</p>
    {/if}

    <div class="catalog-list">
      {#each catalogs as catalog}
        <article class:selected={selectedName === catalog.name} class="catalog-card">
          <div>
            <strong>{catalog.name}</strong>
            <span>{catalog.db_path}</span>
          </div>
          {#if catalog.name === 'default'}
            <button type="button" on:click={useDefault}>Use default</button>
          {:else}
            <input
              bind:value={passwordByCatalog[catalog.name]}
              placeholder="Password"
              type="password"
              aria-label={`Password for ${catalog.name}`}
            />
            <button type="button" on:click={() => load(catalog.name)} disabled={saving}>
              Load
            </button>
          {/if}
        </article>
      {/each}
    </div>
  </section>

  <section class="panel">
    <div>
      <p class="eyebrow">New catalog</p>
      <h2>Create context</h2>
    </div>
    <form class="create-form" on:submit|preventDefault={create}>
      <label>
        Catalog name
        <input bind:value={newCatalogName} placeholder="work" />
      </label>
      <label>
        Password
        <input bind:value={newCatalogPassword} type="password" placeholder="At least 4 characters" />
      </label>
      <button type="submit" disabled={saving || !newCatalogName.trim() || newCatalogPassword.length < 4}>
        Create catalog
      </button>
    </form>
  </section>
</main>

<style>
  .catalog-page {
    display: grid;
    gap: 1rem;
    max-width: 920px;
    margin: 0 auto;
    padding: 1rem;
  }

  .panel {
    background: #fff;
    border: 1px solid #d9e0e8;
    border-radius: 8px;
    display: grid;
    gap: 1rem;
    padding: 1rem;
  }

  .eyebrow {
    color: #687385;
    font-size: 0.78rem;
    font-weight: 700;
    margin: 0 0 0.2rem;
    text-transform: uppercase;
  }

  h1,
  h2 {
    margin: 0;
  }

  .muted,
  .catalog-card span {
    color: #596679;
  }

  .catalog-list,
  .create-form {
    display: grid;
    gap: 0.75rem;
  }

  .catalog-card {
    align-items: center;
    border: 1px solid #cbd7e3;
    border-left: 5px solid #aebdcb;
    border-radius: 6px;
    display: grid;
    gap: 0.75rem;
    grid-template-columns: minmax(0, 1fr) 220px auto;
    padding: 0.75rem;
  }

  .catalog-card.selected {
    border-left-color: #2f80ed;
    background: #f7fbff;
  }

  .catalog-card div {
    display: grid;
    gap: 0.2rem;
  }

  .create-form label {
    color: #4f5d6f;
    display: grid;
    gap: 0.3rem;
  }

  .message {
    background: #edf8ee;
    border: 1px solid #79bd84;
    border-radius: 6px;
    color: #236d33;
    padding: 0.7rem;
  }

  .error {
    background: #fff0f0;
    border: 1px solid #e7a7a7;
    border-radius: 6px;
    color: #9d2525;
    padding: 0.7rem;
  }

  @media (max-width: 760px) {
    .catalog-card {
      grid-template-columns: 1fr;
    }
  }
</style>
