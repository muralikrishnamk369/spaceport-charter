export async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, options);
  const body = await response.json();
  if (!response.ok) {
    const message = typeof body.detail === 'string' ? body.detail : 'Check your inputs and try again.';
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return body;
}
export function centralDay() {
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Chicago', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date());
  const part = name => parts.find(item => item.type === name).value;
  return `${part('year')}-${part('month')}-${part('day')}`;
}
export function centralTime(value) {
  return new Intl.DateTimeFormat('en-US', { timeZone: 'America/Chicago', hour: 'numeric', minute: '2-digit' }).format(new Date(value));
}
export function centralDate(value) {
  return new Intl.DateTimeFormat('en-US', { timeZone: 'America/Chicago', year: 'numeric', month: 'short', day: 'numeric' }).format(new Date(value));
}
