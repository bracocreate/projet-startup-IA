// Lecture côté serveur (rendu des pages) : appelle directement le backend, sans passer par le navigateur.
// En cas d'échec, renvoie null : la page s'affiche quand même et le navigateur retente le chargement
// (avec un message d'erreur explicite s'il échoue aussi).

const TIMEOUT_MS = 3000;

export async function fetchInitial<T>(path: string): Promise<T | null> {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${backendUrl}/api/v1${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    return res.ok ? ((await res.json()) as T) : null;
  } catch {
    return null;
  }
}
