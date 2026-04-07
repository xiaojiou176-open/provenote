import { fireEvent, render, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { EpisodeProfile, SpeakerProfile } from "@/lib/types/podcasts";
import { EpisodeProfileFormDialog } from "./EpisodeProfileFormDialog";

const hoisted = vi.hoisted(() => ({
  createMutateAsync: vi.fn(),
  updateMutateAsync: vi.fn(),
  useCreateEpisodeProfileMock: vi.fn(),
  useUpdateEpisodeProfileMock: vi.fn(),
}));

vi.mock("@/lib/hooks/use-podcasts", () => ({
  useCreateEpisodeProfile: hoisted.useCreateEpisodeProfileMock,
  useUpdateEpisodeProfile: hoisted.useUpdateEpisodeProfileMock,
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

const speakerProfiles: SpeakerProfile[] = [
  {
    id: "sp-1",
    name: "Host Pack",
    description: "",
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
  },
];

const initialData: EpisodeProfile = {
  id: "epf-1",
  name: "Interview",
  description: "desc",
  speaker_config: "Host Pack",
  outline_provider: "google",
  outline_model: "gemini-3.1-pro",
  transcript_provider: "google",
  transcript_model: "gemini-3.1-pro",
  default_briefing: "briefing",
  num_segments: 6,
};

describe("EpisodeProfileFormDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useCreateEpisodeProfileMock.mockReturnValue({
      mutateAsync: hoisted.createMutateAsync,
      isPending: false,
    });
    hoisted.useUpdateEpisodeProfileMock.mockReturnValue({
      mutateAsync: hoisted.updateMutateAsync,
      isPending: false,
    });
    hoisted.createMutateAsync.mockResolvedValue(undefined);
    hoisted.updateMutateAsync.mockResolvedValue(undefined);
  });

  it("submits create payload with defaults and closes dialog", async () => {
    const onOpenChange = vi.fn();
    const { container } = render(
      <EpisodeProfileFormDialog
        mode="create"
        open
        onOpenChange={onOpenChange}
        speakerProfiles={speakerProfiles}
        modelOptions={{ google: ["gemini-3.1-pro"] }}
      />,
    );

    fireEvent.change(container.querySelector("#name") as HTMLInputElement, {
      target: { value: "Weekly Interview" },
    });
    fireEvent.change(container.querySelector("#default_briefing") as HTMLTextAreaElement, {
      target: { value: "Summarize practical insights" },
    });

    fireEvent.submit(container.querySelector("form") as HTMLFormElement);

    await waitFor(() => {
      expect(hoisted.createMutateAsync).toHaveBeenCalledWith({
        name: "Weekly Interview",
        description: "",
        speaker_config: "Host Pack",
        outline_provider: "google",
        outline_model: "gemini-3.1-pro",
        transcript_provider: "google",
        transcript_model: "gemini-3.1-pro",
        default_briefing: "Summarize practical insights",
        num_segments: 5,
      });
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("submits edit payload with profile id", async () => {
    const { container } = render(
      <EpisodeProfileFormDialog
        mode="edit"
        open
        onOpenChange={vi.fn()}
        speakerProfiles={speakerProfiles}
        modelOptions={{ google: ["gemini-3.1-pro"] }}
        initialData={initialData}
      />,
    );

    fireEvent.change(container.querySelector("#name") as HTMLInputElement, {
      target: { value: "Updated Interview" },
    });

    fireEvent.submit(container.querySelector("form") as HTMLFormElement);

    await waitFor(() => {
      expect(hoisted.updateMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          profileId: "epf-1",
          payload: expect.objectContaining({ name: "Updated Interview" }),
        }),
      );
    });
  });

  it("normalizes unavailable models from provider options and supports cancel", async () => {
    const onOpenChange = vi.fn();
    const { container } = render(
      <EpisodeProfileFormDialog
        mode="edit"
        open
        onOpenChange={onOpenChange}
        speakerProfiles={speakerProfiles}
        modelOptions={{ google: ["gemini-3.1-pro-new"] }}
        initialData={{
          ...initialData,
          outline_model: "legacy-outline-model",
          transcript_model: "legacy-transcript-model",
        }}
      />,
    );

    fireEvent.submit(container.querySelector("form") as HTMLFormElement);

    await waitFor(() => {
      expect(hoisted.updateMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          profileId: "epf-1",
          payload: expect.objectContaining({
            outline_model: "gemini-3.1-pro-new",
            transcript_model: "gemini-3.1-pro-new",
          }),
        }),
      );
    });

    fireEvent.click(container.querySelector('button[type="button"]') as HTMLButtonElement);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("renders empty-state alerts when no speaker profiles or providers are available", () => {
    const { getByText } = render(
      <EpisodeProfileFormDialog
        mode="create"
        open
        onOpenChange={vi.fn()}
        speakerProfiles={[]}
        modelOptions={{}}
      />,
    );

    expect(getByText(/no speaker profiles/i)).toBeInTheDocument();
    expect(getByText(/no language models/i)).toBeInTheDocument();
  });
});
