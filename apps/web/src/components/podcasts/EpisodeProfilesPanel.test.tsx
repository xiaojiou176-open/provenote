import { createEvent, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { EpisodeProfile, SpeakerProfile } from "@/lib/types/podcasts";
import { EpisodeProfilesPanel } from "./EpisodeProfilesPanel";

const hoisted = vi.hoisted(() => ({
  deleteMutate: vi.fn(),
  duplicateMutate: vi.fn(),
  useDeleteEpisodeProfileMock: vi.fn(),
  useDuplicateEpisodeProfileMock: vi.fn(),
}));

vi.mock("@/lib/hooks/use-podcasts", () => ({
  useDeleteEpisodeProfile: hoisted.useDeleteEpisodeProfileMock,
  useDuplicateEpisodeProfile: hoisted.useDuplicateEpisodeProfileMock,
}));

vi.mock("@/components/podcasts/forms/EpisodeProfileFormDialog", () => ({
  EpisodeProfileFormDialog: ({
    mode,
    open,
    onOpenChange,
  }: {
    mode: "create" | "edit";
    open: boolean;
    onOpenChange: (open: boolean) => void;
  }) =>
    open ? (
      <div data-testid={`episode-profile-form-${mode}`}>
        <button onClick={() => onOpenChange(false)} type="button">
          close-{mode}
        </button>
      </div>
    ) : null,
}));

vi.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuContent: ({
    children,
    onClick,
  }: {
    children: ReactNode;
    onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
  }) => <div onClick={onClick}>{children}</div>,
  DropdownMenuItem: ({
    children,
    onClick,
    disabled,
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
  }) => (
    <button type="button" disabled={disabled} onClick={onClick}>
      {children}
    </button>
  ),
  DropdownMenuSeparator: () => <hr />,
}));

vi.mock("@/components/ui/alert-dialog", () => ({
  AlertDialog: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: { children: ReactNode }) => <h3>{children}</h3>,
  AlertDialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  AlertDialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogCancel: ({ children }: { children: ReactNode }) => (
    <button type="button">{children}</button>
  ),
  AlertDialogAction: ({
    children,
    onClick,
    disabled,
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
  }) => (
    <button type="button" onClick={onClick} disabled={disabled}>
      {children}
    </button>
  ),
}));

const episodeProfile: EpisodeProfile = {
  id: "epf-1",
  name: "Interview",
  description: "Interview template",
  speaker_config: "Host Pack",
  outline_provider: "google",
  outline_model: "gemini-3.1-pro",
  transcript_provider: "google",
  transcript_model: "gemini-3.1-pro",
  default_briefing: "Keep it practical",
  num_segments: 6,
};

const speakerProfile: SpeakerProfile = {
  id: "sp-1",
  name: "Host Pack",
  description: "Main speakers",
  tts_provider: "openai",
  tts_model: "gpt-4o-mini-tts",
  speakers: [
    {
      name: "A",
      voice_id: "voice-a",
      backstory: "host",
      personality: "warm",
    },
  ],
};

describe("EpisodeProfilesPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useDeleteEpisodeProfileMock.mockReturnValue({
      mutate: hoisted.deleteMutate,
      isPending: false,
    });
    hoisted.useDuplicateEpisodeProfileMock.mockReturnValue({
      mutate: hoisted.duplicateMutate,
      isPending: false,
    });
  });

  it("disables create when no speaker profiles exist", () => {
    render(
      <EpisodeProfilesPanel
        episodeProfiles={[]}
        speakerProfiles={[]}
        modelOptions={{ google: ["gemini-3.1-pro"] }}
      />,
    );

    expect(screen.getByRole("button", { name: /create profile/i })).toBeDisabled();
    expect(
      screen.getByText("Create a speaker profile before adding an episode profile."),
    ).toBeInTheDocument();
  });

  it("handles duplicate, delete, and edit actions", () => {
    render(
      <EpisodeProfilesPanel
        episodeProfiles={[episodeProfile]}
        speakerProfiles={[speakerProfile]}
        modelOptions={{ google: ["gemini-3.1-pro"] }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /duplicate/i }));
    expect(hoisted.duplicateMutate).toHaveBeenCalledWith("epf-1");

    const deleteButtons = screen.getAllByRole("button", { name: /^delete$/i });
    fireEvent.click(deleteButtons[deleteButtons.length - 1]);
    expect(hoisted.deleteMutate).toHaveBeenCalledWith("epf-1");

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));
    expect(screen.getByTestId("episode-profile-form-edit")).toBeInTheDocument();
  });

  it("opens create dialog and disables menu actions while duplicate/delete are pending", () => {
    hoisted.useDeleteEpisodeProfileMock.mockReturnValue({
      mutate: hoisted.deleteMutate,
      isPending: true,
    });
    hoisted.useDuplicateEpisodeProfileMock.mockReturnValue({
      mutate: hoisted.duplicateMutate,
      isPending: true,
    });

    render(
      <EpisodeProfilesPanel
        episodeProfiles={[episodeProfile]}
        speakerProfiles={[speakerProfile]}
        modelOptions={{ google: ["gemini-3.1-pro"] }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /create profile/i }));
    expect(screen.getByTestId("episode-profile-form-create")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "close-create" }));
    expect(screen.queryByTestId("episode-profile-form-create")).not.toBeInTheDocument();

    expect(screen.getByRole("button", { name: /duplicate/i })).toBeDisabled();
  });

  it("clears edit dialog state when edit form closes", () => {
    render(
      <EpisodeProfilesPanel
        episodeProfiles={[episodeProfile]}
        speakerProfiles={[speakerProfile]}
        modelOptions={{ google: ["gemini-3.1-pro"] }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));
    expect(screen.getByTestId("episode-profile-form-edit")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "close-edit" }));
    expect(screen.queryByTestId("episode-profile-form-edit")).not.toBeInTheDocument();
  });

  it("renders fallback description, speaker badge, and briefing copy", () => {
    render(
      <EpisodeProfilesPanel
        episodeProfiles={[
          {
            ...episodeProfile,
            description: "",
            default_briefing: "Use a calm opening",
          },
        ]}
        speakerProfiles={[speakerProfile]}
        modelOptions={{ google: ["gemini-3.1-pro"] }}
      />,
    );

    expect(screen.getByText("No description provided.")).toBeInTheDocument();
    expect(screen.getByText("openai / gpt-4o-mini-tts")).toBeInTheDocument();
    expect(screen.getByText("Use a calm opening")).toBeInTheDocument();
    expect(screen.getByText(/Delete profile/i)).toBeInTheDocument();
  });

  it("stops propagation on actions trigger and menu content clicks", () => {
    render(
      <EpisodeProfilesPanel
        episodeProfiles={[episodeProfile]}
        speakerProfiles={[speakerProfile]}
        modelOptions={{ google: ["gemini-3.1-pro"] }}
      />,
    );

    const actionsButton = screen.getByRole("button", { name: "Actions" });
    const triggerEvent = createEvent.click(actionsButton);
    triggerEvent.stopPropagation = vi.fn();
    fireEvent(actionsButton, triggerEvent);
    expect(triggerEvent.stopPropagation).toHaveBeenCalled();

    const duplicateItem = screen.getByRole("button", { name: "Duplicate" });
    const menuEvent = createEvent.click(duplicateItem);
    menuEvent.stopPropagation = vi.fn();
    fireEvent(duplicateItem.parentElement as HTMLElement, menuEvent);
    expect(menuEvent.stopPropagation).toHaveBeenCalled();
  });
});
