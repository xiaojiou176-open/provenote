import { createEvent, fireEvent, render, screen, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SpeakerProfile } from "@/lib/types/podcasts";
import { SpeakerProfilesPanel } from "./SpeakerProfilesPanel";

const hoisted = vi.hoisted(() => ({
  deleteMutate: vi.fn(),
  duplicateMutate: vi.fn(),
  useDeleteSpeakerProfileMock: vi.fn(),
  useDuplicateSpeakerProfileMock: vi.fn(),
}));

vi.mock("@/lib/hooks/use-podcasts", () => ({
  useDeleteSpeakerProfile: hoisted.useDeleteSpeakerProfileMock,
  useDuplicateSpeakerProfile: hoisted.useDuplicateSpeakerProfileMock,
}));

vi.mock("@/components/podcasts/forms/SpeakerProfileFormDialog", () => ({
  SpeakerProfileFormDialog: ({
    mode,
    open,
    onOpenChange,
  }: {
    mode: "create" | "edit";
    open: boolean;
    onOpenChange: (open: boolean) => void;
  }) =>
    open ? (
      <div data-testid={`speaker-profile-form-${mode}`}>
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

const speakerA: SpeakerProfile = {
  id: "sp-1",
  name: "Host Pack",
  description: "Main hosts",
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

const speakerB: SpeakerProfile = {
  id: "sp-2",
  name: "Guest Pack",
  description: "Guests",
  tts_provider: "openai",
  tts_model: "gpt-4o-mini-tts",
  speakers: [
    {
      name: "B",
      voice_id: "voice-b",
      backstory: "guest",
      personality: "calm",
    },
  ],
};

describe("SpeakerProfilesPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useDeleteSpeakerProfileMock.mockReturnValue({
      mutate: hoisted.deleteMutate,
      isPending: false,
    });
    hoisted.useDuplicateSpeakerProfileMock.mockReturnValue({
      mutate: hoisted.duplicateMutate,
      isPending: false,
    });
  });

  it("allows duplicate and delete for unused profiles", () => {
    render(
      <SpeakerProfilesPanel
        speakerProfiles={[speakerA]}
        modelOptions={{ openai: ["gpt-4o-mini-tts"] }}
        usage={{ "Host Pack": 0 }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /duplicate/i }));
    expect(hoisted.duplicateMutate).toHaveBeenCalledWith("sp-1");

    const deleteButtons = screen.getAllByRole("button", { name: /^delete$/i });
    fireEvent.click(deleteButtons[deleteButtons.length - 1]);
    expect(hoisted.deleteMutate).toHaveBeenCalledWith("sp-1");
  });

  it("disables delete when profile is in use", () => {
    render(
      <SpeakerProfilesPanel
        speakerProfiles={[speakerA, speakerB]}
        modelOptions={{ openai: ["gpt-4o-mini-tts"] }}
        usage={{ "Host Pack": 2, "Guest Pack": 0 }}
      />,
    );

    const hostPackCard = screen.getByText("Host Pack").closest(".shadow-sm");
    expect(hostPackCard).not.toBeNull();

    const hostDeleteButtons = within(hostPackCard as HTMLElement).getAllByRole("button", {
      name: /^delete$/i,
    });
    hostDeleteButtons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it("opens create/edit dialogs and disables duplicate while pending", () => {
    hoisted.useDuplicateSpeakerProfileMock.mockReturnValue({
      mutate: hoisted.duplicateMutate,
      isPending: true,
    });

    render(
      <SpeakerProfilesPanel
        speakerProfiles={[speakerA]}
        modelOptions={{ openai: ["gpt-4o-mini-tts"] }}
        usage={{ "Host Pack": 0 }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /create speaker/i }));
    expect(screen.getByTestId("speaker-profile-form-create")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "close-create" }));
    expect(screen.queryByTestId("speaker-profile-form-create")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));
    expect(screen.getByTestId("speaker-profile-form-edit")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "close-edit" }));
    expect(screen.queryByTestId("speaker-profile-form-edit")).not.toBeInTheDocument();

    expect(screen.getByRole("button", { name: /duplicate/i })).toBeDisabled();
  });

  it("renders delete-disabled hint for in-use profile and empty state when missing", () => {
    const { rerender } = render(
      <SpeakerProfilesPanel
        speakerProfiles={[speakerA]}
        modelOptions={{ openai: ["gpt-4o-mini-tts"] }}
        usage={{ "Host Pack": 3 }}
      />,
    );

    expect(screen.getByText(/used by 3 episodes/i)).toBeInTheDocument();
    expect(
      screen.getByText("Remove this speaker from episode profiles before deleting it."),
    ).toBeInTheDocument();
    expect(screen.getByText("host")).toBeInTheDocument();

    rerender(
      <SpeakerProfilesPanel
        speakerProfiles={[]}
        modelOptions={{ openai: ["gpt-4o-mini-tts"] }}
        usage={{}}
      />,
    );

    expect(
      screen.getByText("No speaker profiles yet. Create one to make episode templates available."),
    ).toBeInTheDocument();
  });

  it("stops propagation on actions trigger and menu content clicks", () => {
    render(
      <SpeakerProfilesPanel
        speakerProfiles={[speakerA]}
        modelOptions={{ openai: ["gpt-4o-mini-tts"] }}
        usage={{ "Host Pack": 0 }}
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
