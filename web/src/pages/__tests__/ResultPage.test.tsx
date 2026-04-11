// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import ResultPage from "../ResultPage";
import { saveStudentResult } from "../../data/demoSession";
import { storedResult, studentSessionId } from "./studentFixtures";

describe("ResultPage smoke flow", () => {
  beforeEach(() => {
    sessionStorage.clear();
    saveStudentResult(storedResult);
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  it("renders the scored breakdown and returns to the session route", async () => {
    render(
      <MemoryRouter initialEntries={[`/practice/${studentSessionId}/result`]}>
        <Routes>
          <Route path="/practice/:sessionId/result" element={<ResultPage />} />
          <Route path="/practice/:sessionId" element={<div>Practice session stub</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: /interview ready/i })).toBeInTheDocument();
    expect(screen.getByText(/how the answer was read/i)).toBeInTheDocument();
    expect(screen.getByText(/what stands out/i)).toBeInTheDocument();
    expect(screen.getByText(/use the result to keep the loop moving/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /back to session/i }));

    expect(await screen.findByText(/practice session stub/i)).toBeInTheDocument();
  });
});
