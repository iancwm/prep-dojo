export class ApiError extends Error {
  status: number;
  detail: unknown;
  path: string;
  requestLabel?: string;

  constructor(message: string, status: number, detail: unknown, path: string, requestLabel?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.path = path;
    this.requestLabel = requestLabel;
  }
}

function serializeDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object" && "msg" in item) {
          const msg = (item as { msg?: unknown }).msg;
          return typeof msg === "string" ? msg : JSON.stringify(item);
        }
        return JSON.stringify(item);
      })
      .join(", ");
  }

  if (detail && typeof detail === "object" && "detail" in detail) {
    return serializeDetail((detail as { detail: unknown }).detail);
  }

  return "Request failed.";
}

async function parseResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function formatErrorMessage(path: string, status: number, detail: unknown, requestLabel?: string): string {
  const prefix = requestLabel ?? `Request to ${path}`;
  const bodyMessage = serializeDetail(detail);

  if (status === 404) {
    return `${prefix} failed: endpoint returned 404 Not Found.`;
  }

  if (status === 422) {
    return `${prefix} failed validation: ${bodyMessage}`;
  }

  if (bodyMessage && bodyMessage !== "Request failed.") {
    return `${prefix} failed: ${bodyMessage}`;
  }

  return `${prefix} failed with status ${status}.`;
}

export async function requestJson<T>(
  path: string,
  init: RequestInit = {},
  options: { requestLabel?: string } = {}
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, {
    ...init,
    headers,
  });

  const hasBody = response.status !== 204;
  if (!response.ok) {
    const detail = hasBody ? await parseResponseBody(response) : null;
    throw new ApiError(
      formatErrorMessage(path, response.status, detail, options.requestLabel),
      response.status,
      detail ?? { message: response.statusText },
      path,
      options.requestLabel
    );
  }

  if (!hasBody) {
    return undefined as T;
  }

  return (await parseResponseBody(response)) as T;
}

export function toQueryString(params: Record<string, string | number | boolean | null | undefined>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") {
      continue;
    }
    query.set(key, String(value));
  }
  const text = query.toString();
  return text ? `?${text}` : "";
}
