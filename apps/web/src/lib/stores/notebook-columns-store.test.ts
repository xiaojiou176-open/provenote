import { act } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useNotebookColumnsStore } from "./notebook-columns-store";

describe("notebook-columns-store", () => {
  beforeEach(() => {
    localStorage.clear();
    useNotebookColumnsStore.setState({
      sourcesCollapsed: false,
      notesCollapsed: false,
    });
  });

  it("toggles sources and notes columns independently", () => {
    act(() => {
      useNotebookColumnsStore.getState().toggleSources();
      useNotebookColumnsStore.getState().toggleNotes();
    });

    expect(useNotebookColumnsStore.getState().sourcesCollapsed).toBe(true);
    expect(useNotebookColumnsStore.getState().notesCollapsed).toBe(true);
  });

  it("sets collapse state explicitly and exposes persist key", () => {
    act(() => {
      useNotebookColumnsStore.getState().setSources(true);
      useNotebookColumnsStore.getState().setNotes(false);
    });

    expect(useNotebookColumnsStore.getState().sourcesCollapsed).toBe(true);
    expect(useNotebookColumnsStore.getState().notesCollapsed).toBe(false);
    expect(useNotebookColumnsStore.persist.getOptions().name).toBe("notebook-columns-storage");
  });
});
