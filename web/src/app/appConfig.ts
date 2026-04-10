export const appConfig = {
  brandName: "Prep Dojo",
  productLine: "Demo shell",
  apiBaseUrl: "http://127.0.0.1:8000",
};

export const flowSteps = [
  { title: "Create", detail: "Operator drafts credible practice content." },
  { title: "Practice", detail: "Student runs a realistic session." },
  { title: "Review", detail: "The result shows up in the system." },
] as const;
