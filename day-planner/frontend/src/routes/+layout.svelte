<script lang="ts">
  import { page } from '$app/stores';
</script>

<nav class="top-nav">
  <a class:active={$page.url.pathname === '/'} href="/">Planner</a>
  <a class:active={$page.url.pathname === '/tasks'} href="/tasks">Tasks</a>
  <a class:active={$page.url.pathname === '/habits'} href="/habits">Habits</a>
  <a class:active={$page.url.pathname === '/projects'} href="/projects">Projects</a>
  <a class:active={$page.url.pathname === '/catalogs'} href="/catalogs">Catalogs</a>
</nav>

<slot />

<style>
  :global(body) {
    margin: 0;
    background: #f5f6f8;
    color: #1f2933;
    font-family:
      Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }

  :global(button),
  :global(input),
  :global(select),
  :global(textarea) {
    font: inherit;
  }

  :global(button) {
    border: 1px solid #c9d2dc;
    border-radius: 6px;
    background: #fff;
    color: #1f2933;
    cursor: pointer;
    padding: 0.45rem 0.65rem;
  }

  :global(button:disabled) {
    cursor: not-allowed;
    opacity: 0.55;
  }

  :global(input),
  :global(select),
  :global(textarea) {
    border: 1px solid #c9d2dc;
    border-radius: 6px;
    box-sizing: border-box;
    padding: 0.55rem 0.65rem;
    width: 100%;
  }

  .top-nav {
    align-items: center;
    background: #fff;
    border-bottom: 1px solid #d9e0e8;
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
  }

  .top-nav a {
    border-radius: 6px;
    color: #405064;
    padding: 0.45rem 0.7rem;
    text-decoration: none;
  }

  .top-nav a.active {
    background: #e8f2ff;
    color: #1d5fb8;
    font-weight: 700;
  }
</style>
