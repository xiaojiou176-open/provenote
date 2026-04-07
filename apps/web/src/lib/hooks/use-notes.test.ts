import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { useCreateNote, useDeleteNote, useNote, useNotes, useUpdateNote } from "./use-notes";

const hoisted = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  useAppMutationMock: vi.fn(),
  getApiErrorKeyMock: vi.fn(),
  listMock: vi.fn(),
  getMock: vi.fn(),
  createMock: vi.fn(),
  updateMock: vi.fn(),
  deleteMock: vi.fn(),
  queryClient: {
    invalidateQueries: vi.fn(),
  },
  t: Object.assign((key: string) => key, {
    common: {
      success: "Success",
      error: "Error",
    },
    notebooks: {
      noteCreatedSuccess: "Created",
      failedToCreateNote: "Create failed",
      noteUpdatedSuccess: "Updated",
      failedToUpdateNote: "Update failed",
      noteDeletedSuccess: "Deleted",
      failedToDeleteNote: "Delete failed",
    },
  }),
}));

vi.mock("@/lib/api/notes", () => ({
  notesApi: {
    list: hoisted.listMock,
    get: hoisted.getMock,
    create: hoisted.createMock,
    update: hoisted.updateMock,
    delete: hoisted.deleteMock,
  },
}));

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: hoisted.useQueryMock,
    useQueryClient: hoisted.useQueryClientMock,
  };
});

vi.mock("@/lib/hooks/use-app-mutation", () => ({
  useAppMutation: hoisted.useAppMutationMock,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: hoisted.t }),
}));

vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorKey: hoisted.getApiErrorKeyMock,
}));

describe("useNotes hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useQueryClientMock.mockReturnValue(hoisted.queryClient);
    hoisted.useAppMutationMock.mockImplementation((options: unknown) => options);
    hoisted.getApiErrorKeyMock.mockReturnValue("resolved.error");
  });

  it("scopes notes query by notebook id and executes list query function", async () => {
    hoisted.listMock.mockResolvedValue([]);

    const { result } = renderHook(() => useNotes("nb-42"));

    expect(result.current.queryKey).toEqual(QUERY_KEYS.notes("nb-42"));
    expect(result.current.enabled).toBe(true);

    await result.current.queryFn();
    expect(hoisted.listMock).toHaveBeenCalledWith({ notebook_id: "nb-42" });

    const { result: disabled } = renderHook(() => useNotes(undefined));
    expect(disabled.current.enabled).toBe(false);
  });

  it("respects explicit disabling of single note query and executes detail query function", async () => {
    hoisted.getMock.mockResolvedValue({ id: "note-1" });

    const { result } = renderHook(() => useNote("note-1", { enabled: false }));
    expect(result.current.queryKey).toEqual(QUERY_KEYS.note("note-1"));
    expect(result.current.enabled).toBe(false);

    await result.current.queryFn();
    expect(hoisted.getMock).toHaveBeenCalledWith("note-1");
  });

  it("disables note query when id is missing", () => {
    const { result } = renderHook(() => useNote(undefined));
    expect(result.current.queryKey).toEqual(QUERY_KEYS.note(""));
    expect(result.current.enabled).toBe(false);
  });

  it("enables note query when id is present and options are omitted", () => {
    const { result } = renderHook(() => useNote("note-2"));
    expect(result.current.enabled).toBe(true);
  });

  it("creates note and exposes localized success/error config", async () => {
    hoisted.createMock.mockResolvedValue({ id: "new-note" });
    const { result } = renderHook(() => useCreateNote());

    await result.current.mutationFn({ notebook_id: "nb-1", title: "New note" });
    result.current.onSuccess?.({}, { notebook_id: "nb-1" });
    result.current.errorToast?.(new Error("create failed"));

    expect(hoisted.createMock).toHaveBeenCalledWith({ notebook_id: "nb-1", title: "New note" });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.notes("nb-1"),
    });
    expect(result.current.successToast).toEqual({
      title: "Success",
      description: "Created",
    });
    expect(hoisted.getApiErrorKeyMock).toHaveBeenCalledWith(expect.any(Error), "Create failed");
  });

  it("updates note and invalidates list/detail queries", async () => {
    hoisted.updateMock.mockResolvedValue({ id: "note-9" });
    const { result } = renderHook(() => useUpdateNote());

    await result.current.mutationFn({ id: "note-9", data: { title: "Updated" } });
    result.current.onSuccess?.({}, { id: "note-9", data: { title: "Updated" } });
    result.current.errorToast?.(new Error("update failed"));

    expect(hoisted.updateMock).toHaveBeenCalledWith("note-9", { title: "Updated" });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.notes(),
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.note("note-9"),
    });
    expect(hoisted.getApiErrorKeyMock).toHaveBeenCalledWith(expect.any(Error), "Update failed");
  });

  it("deletes note and invalidates global notes cache", async () => {
    hoisted.deleteMock.mockResolvedValue(undefined);
    const { result } = renderHook(() => useDeleteNote());

    await result.current.mutationFn("note-9");
    result.current.onSuccess?.();
    result.current.errorToast?.(new Error("delete failed"));

    expect(hoisted.deleteMock).toHaveBeenCalledWith("note-9");
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({ queryKey: ["notes"] });
    expect(hoisted.getApiErrorKeyMock).toHaveBeenCalledWith(expect.any(Error), "Delete failed");
  });
});
