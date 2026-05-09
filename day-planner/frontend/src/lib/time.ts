export function minutesToTimeLabel(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
}

export function timeLabelToMinutes(label: string): number {
  const [hours, minutes] = label.split(':').map(Number);
  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) {
    throw new Error('Use HH:MM format');
  }
  return hours * 60 + minutes;
}

export function snapToIncrement(minutes: number, increment = 15): number {
  return Math.round(minutes / increment) * increment;
}

export function todayISODate(): string {
  const now = new Date();
  const offsetMs = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offsetMs).toISOString().slice(0, 10);
}
