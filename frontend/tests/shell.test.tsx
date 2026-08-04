/** @vitest-environment jsdom */

import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it } from "vitest";

import { AppShell } from "../src/components/AppShell";
import { AppStateProvider } from "../src/state/appState";

afterEach(cleanup);

describe("F02 application shell", () => {
  it("puts the skip link first and locks later chapters until data exists", () => {
    render(
      <AppStateProvider>
        <AppShell>
          <h1>Shell content</h1>
        </AppShell>
      </AppStateProvider>,
    );

    const skipLink = screen.getByRole("link", { name: "Skip to main content" });
    expect(document.querySelector(".app-frame")?.firstElementChild).toBe(skipLink);
    expect(screen.getByRole("button", { name: /Tomorrow's Brief/ })).not.toBeDisabled();
    expect(screen.getByRole("button", { name: /Plan Transformation/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Why \/ What-if/ })).toBeDisabled();
    expect(screen.getByRole("status", { name: /Solver evidence status/ })).toHaveTextContent("WAITING");
  });

  it("keeps the policy boundary visible in the bottom trust bar", () => {
    render(
      <AppStateProvider>
        <AppShell>
          <h1>Shell content</h1>
        </AppShell>
      </AppStateProvider>,
    );

    expect(screen.getByRole("contentinfo")).toHaveTextContent(
      "Not medical, legal, or workplace-safety guidance",
    );
    expect(screen.getByRole("main")).toBeVisible();
  });

  it("moves focus to main content from the skip link", () => {
    render(
      <AppStateProvider>
        <AppShell>
          <h1>Shell content</h1>
        </AppShell>
      </AppStateProvider>,
    );

    fireEvent.click(screen.getByRole("link", { name: "Skip to main content" }));

    expect(document.activeElement).toBe(screen.getByRole("main"));
  });
});
