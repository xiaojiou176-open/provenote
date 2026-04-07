import { useQueryClient } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  TRANSFORMATION_QUERY_KEYS,
  useCreateTransformation,
  useTransformation,
  useUpdateTransformation,
} from "@/lib/hooks/use-transformations";
import type { Transformation } from "@/lib/types/transformations";
import { TransformationEditorDialog } from "./TransformationEditorDialog";

const invalidateQueries = vi.fn();
const createMutateAsync = vi.fn();
const updateMutateAsync = vi.fn();

vi.mock("@tanstack/react-query", async () => {
  const actual =
    await vi.importActual<typeof import("@tanstack/react-query")>("@tanstack/react-query");
  return {
    ...actual,
    useQueryClient: vi.fn(),
  };
});

vi.mock("@/lib/hooks/use-transformations", async () => {
  const actual = await vi.importActual<typeof import("@/lib/hooks/use-transformations")>(
    "@/lib/hooks/use-transformations",
  );
  return {
    ...actual,
    useTransformation: vi.fn(),
    useCreateTransformation: vi.fn(),
    useUpdateTransformation: vi.fn(),
  };
});

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      common: {
        cancel: "Cancel",
        loading: "Loading",
        creating: "Creating",
        saving: "Saving",
        title: "Title",
        edit: "Edit",
        editTransformation: "Edit Transformation",
      },
      transformations: {
        createNew: "Create New",
        name: "Name",
        namePlaceholder: "Transformation name",
        titlePlaceholder: "Transformation title",
        suggestDefault: "Suggest as default",
        descriptionPlaceholder: "Describe transformation",
        systemPrompt: "System Prompt",
        promptPlaceholder: "Write prompt",
        promptHint: "Prompt hint",
      },
      notebooks: {
        addDescription: "Add description...",
      },
    },
  }),
}));

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({
    open,
    children,
  }: {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    children: ReactNode;
  }) => (open ? <div data-testid="dialog-root">{children}</div> : null),
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
}));

vi.mock("@/components/ui/markdown-editor", () => ({
  MarkdownEditor: ({
    value,
    onChange,
    placeholder,
    textareaId,
  }: {
    value: string;
    onChange: (value: string) => void;
    placeholder: string;
    textareaId?: string;
  }) => (
    <textarea
      id={textareaId}
      aria-label={placeholder}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  ),
}));

vi.mock("@/components/ui/checkbox", () => ({
  Checkbox: ({
    id,
    checked,
    onCheckedChange,
  }: {
    id?: string;
    checked?: boolean;
    onCheckedChange?: (checked: boolean) => void;
  }) => (
    <input
      id={id}
      type="checkbox"
      checked={Boolean(checked)}
      onChange={(event) => onCheckedChange?.(event.target.checked)}
    />
  ),
}));

describe("TransformationEditorDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useQueryClient).mockReturnValue({
      invalidateQueries,
    } as unknown as ReturnType<typeof useQueryClient>);

    vi.mocked(useTransformation).mockReturnValue({
      data: undefined,
      isLoading: false,
    } as unknown as ReturnType<typeof useTransformation>);

    vi.mocked(useCreateTransformation).mockReturnValue({
      mutateAsync: createMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateTransformation>);

    vi.mocked(useUpdateTransformation).mockReturnValue({
      mutateAsync: updateMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateTransformation>);
  });

  it("creates a transformation and closes dialog", async () => {
    const onOpenChange = vi.fn();
    createMutateAsync.mockResolvedValue(undefined);

    render(<TransformationEditorDialog open onOpenChange={onOpenChange} />);

    fireEvent.change(screen.getByPlaceholderText("Transformation name"), {
      target: { value: "summary" },
    });
    fireEvent.change(screen.getByPlaceholderText("Transformation title"), {
      target: { value: "Summary" },
    });
    fireEvent.change(screen.getByPlaceholderText("Describe transformation"), {
      target: { value: "Summarize source content" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Write prompt" }), {
      target: { value: "Summarize input in bullet points" },
    });
    fireEvent.click(screen.getByLabelText("Suggest as default"));

    fireEvent.click(screen.getByRole("button", { name: "Create New" }));

    await waitFor(() => {
      expect(createMutateAsync).toHaveBeenCalledWith({
        name: "summary",
        title: "Summary",
        description: "Summarize source content",
        prompt: "Summarize input in bullet points",
        apply_default: true,
      });
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("edits transformation from fetched detail and invalidates detail query", async () => {
    const onOpenChange = vi.fn();
    const baseTransformation: Transformation = {
      id: "tr-1",
      name: "original",
      title: "Original",
      description: "Original description",
      prompt: "Original prompt",
      apply_default: false,
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-01T00:00:00Z",
    };

    vi.mocked(useTransformation).mockReturnValue({
      data: {
        ...baseTransformation,
        name: "fetched-name",
        title: "Fetched Title",
        description: "Fetched Description",
        prompt: "Fetched prompt",
        apply_default: true,
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useTransformation>);

    updateMutateAsync.mockResolvedValue(undefined);

    render(
      <TransformationEditorDialog
        open
        onOpenChange={onOpenChange}
        transformation={baseTransformation}
      />,
    );

    expect(screen.getByDisplayValue("fetched-name")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Write prompt" }), {
      target: { value: "Updated prompt" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Edit Transformation" }));

    await waitFor(() => {
      expect(updateMutateAsync).toHaveBeenCalledWith({
        id: "tr-1",
        data: {
          name: "fetched-name",
          title: "Fetched Title",
          description: "Fetched Description",
          prompt: "Updated prompt",
          apply_default: true,
        },
      });
      expect(invalidateQueries).toHaveBeenCalledWith({
        queryKey: TRANSFORMATION_QUERY_KEYS.transformation("tr-1"),
      });
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("shows loading state when editing and detail is still loading", () => {
    const baseTransformation: Transformation = {
      id: "tr-2",
      name: "draft",
      title: "Draft",
      description: "",
      prompt: "prompt",
      apply_default: false,
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-01T00:00:00Z",
    };

    vi.mocked(useTransformation).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as unknown as ReturnType<typeof useTransformation>);

    render(
      <TransformationEditorDialog
        open
        onOpenChange={vi.fn()}
        transformation={baseTransformation}
      />,
    );

    expect(screen.getByText("Loading")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Edit Transformation" })).toBeDisabled();
  });
});
