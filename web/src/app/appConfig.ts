const defaultApiBaseUrl = "http://127.0.0.1:8010";

export const appConfig = {
  brandName: "Prep Dojo",
  productLine: "Demo shell",
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_TARGET || defaultApiBaseUrl,
};

export const flowSteps = [
  { title: "Create", detail: "Operator drafts credible practice content." },
  { title: "Practice", detail: "Student runs a realistic session." },
  { title: "Review", detail: "The result shows up in the system." },
] as const;
