import { fireEvent, render, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SpeakerProfile } from "@/lib/types/podcasts";
import { SpeakerProfileFormDialog } from "./SpeakerProfileFormDialog";

const hoisted = vi.hoisted(() => ({
  createMutateAsync: vi.fn(),
  updateMutateAsync: vi.fn(),
  useCreateSpeakerProfileMock: vi.fn(),
  useUpdateSpeakerProfileMock: vi.fn(),
}));

vi.mock("@/lib/hooks/use-podcasts", () => ({
  useCreateSpeakerProfile: hoisted.useCreateSpeakerProfileMock,
  useUpdateSpeakerProfile: hoisted.useUpdateSpeakerProfileMock,
}));

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div>{children}</div> : null,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
}));

vi.mock("@/components/ui/select", () => ({
  Select: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectTrigger: ({ id, children }: { id?: string; children: ReactNode }) => (
    <div data-testid={id}>{children}</div>
  ),
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

const initialData: SpeakerProfile = {
  id: "sp-1",
  name: "Host Pack",
  description: "desc",
  tts_provider: "openai",
  tts_model: "gpt-4o-mini-tts",
  speakers: [
    {
      name: "Host",
      voice_id: "voice-host",
      backstory: "host",
      personality: "warm",
    },
  ],
};

describe("SpeakerProfileFormDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useCreateSpeakerProfileMock.mockReturnValue({
      mutateAsync: hoisted.createMutateAsync,
      isPending: false,
    });
    hoisted.useUpdateSpeakerProfileMock.mockReturnValue({
      mutateAsync: hoisted.updateMutateAsync,
      isPending: false,
    });
    hoisted.createMutateAsync.mockResolvedValue(undefined);
    hoisted.updateMutateAsync.mockResolvedValue(undefined);
  });

  it("submits create payload for speaker profile", async () => {
    const onOpenChange = vi.fn();
    const { container } = render(
      <SpeakerProfileFormDialog
        mode="create"
        open
        onOpenChange={onOpenChange}
        modelOptions={{ openai: ["gpt-4o-mini-tts"] }}
      />,
    );

    fireEvent.change(container.querySelector("#name") as HTMLInputElement, {
      target: { value: "Main Cast" },
    });
    fireEvent.change(container.querySelector("#speaker-name-0") as HTMLInputElement, {
      target: { value: "Host" },
    });
    fireEvent.change(container.querySelector("#speaker-voice-0") as HTMLInputElement, {
      target: { value: "voice-host" },
    });
    fireEvent.change(container.querySelector("#speaker-backstory-0") as HTMLTextAreaElement, {
      target: { value: "Story" },
    });
    fireEvent.change(container.querySelector("#speaker-personality-0") as HTMLTextAreaElement, {
      target: { value: "Warm" },
    });

    fireEvent.submit(container.querySelector("form") as HTMLFormElement);

    await waitFor(() => {
      expect(hoisted.createMutateAsync).toHaveBeenCalledWith({
        name: "Main Cast",
        description: "",
        tts_provider: "openai",
        tts_model: "gpt-4o-mini-tts",
        speakers: [
          {
            name: "Host",
            voice_id: "voice-host",
            backstory: "Story",
            personality: "Warm",
          },
        ],
      });
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("submits edit payload with profile id", async () => {
    const { container } = render(
      <SpeakerProfileFormDialog
        mode="edit"
        open
        onOpenChange={vi.fn()}
        modelOptions={{ openai: ["gpt-4o-mini-tts"] }}
        initialData={initialData}
      />,
    );

    fireEvent.change(container.querySelector("#name") as HTMLInputElement, {
      target: { value: "Updated Host Pack" },
    });

    fireEvent.submit(container.querySelector("form") as HTMLFormElement);

    await waitFor(() => {
      expect(hoisted.updateMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          profileId: "sp-1",
          payload: expect.objectContaining({ name: "Updated Host Pack" }),
        }),
      );
    });
  });

  it("normalizes unavailable tts model from selected provider", async () => {
    const { container } = render(
      <SpeakerProfileFormDialog
        mode="edit"
        open
        onOpenChange={vi.fn()}
        modelOptions={{ openai: ["gpt-4o-realtime-preview"] }}
        initialData={{ ...initialData, tts_model: "legacy-model" }}
      />,
    );

    fireEvent.submit(container.querySelector("form") as HTMLFormElement);

    await waitFor(() => {
      expect(hoisted.updateMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          profileId: "sp-1",
          payload: expect.objectContaining({
            tts_model: "gpt-4o-realtime-preview",
          }),
        }),
      );
    });
  });

  it("adds/removes speakers and closes via cancel action", async () => {
    const onOpenChange = vi.fn();
    const { container } = render(
      <SpeakerProfileFormDialog
        mode="create"
        open
        onOpenChange={onOpenChange}
        modelOptions={{ openai: ["gpt-4o-mini-tts"] }}
      />,
    );

    fireEvent.click(container.querySelector('button[type="button"]') as HTMLButtonElement);
    const removeButtons = Array.from(container.querySelectorAll('button[type="button"]')).filter(
      (button) => button.textContent?.toLowerCase().includes("remove"),
    );
    fireEvent.click(removeButtons[0] as HTMLButtonElement);

    const cancelButtons = Array.from(container.querySelectorAll('button[type="button"]')).filter(
      (button) => button.textContent?.toLowerCase().includes("cancel"),
    );
    fireEvent.click(cancelButtons[0] as HTMLButtonElement);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("handles closed dialog defaults and empty-provider configuration", () => {
    render(
      <SpeakerProfileFormDialog
        mode="create"
        open={false}
        onOpenChange={vi.fn()}
        modelOptions={{ openai: [] }}
      />,
    );

    render(
      <SpeakerProfileFormDialog mode="create" open onOpenChange={vi.fn()} modelOptions={{}} />,
    );
  });
});
