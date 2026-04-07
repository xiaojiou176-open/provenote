import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { PodcastEpisode } from "@/lib/types/podcasts";
import { EpisodeCard } from "./EpisodeCard";

const hoisted = vi.hoisted(() => ({
  resolvePodcastAssetUrlMock: vi.fn(),
  revokeObjectUrlMock: vi.fn(),
}));
let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

vi.mock("@/lib/api/podcasts", () => ({
  resolvePodcastAssetUrl: hoisted.resolvePodcastAssetUrlMock,
}));

vi.mock("@/lib/auth-storage", () => ({
  getStoredAuthToken: () => null,
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

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
}));

vi.mock("@/components/ui/tabs", () => ({
  Tabs: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  TabsList: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  TabsTrigger: ({ children }: { children: ReactNode }) => <button type="button">{children}</button>,
  TabsContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

const episode: PodcastEpisode = {
  id: "ep-1",
  name: "Weekly Brief",
  episode_profile: {
    id: "profile-1",
    name: "Profile",
    description: "desc",
    speaker_config: "Host",
    outline_provider: "google",
    outline_model: "gemini-3.1-pro",
    transcript_provider: "google",
    transcript_model: "gemini-3.1-pro",
    default_briefing: "brief",
    num_segments: 5,
  },
  speaker_profile: {
    id: "speaker-1",
    name: "Host",
    description: "desc",
    tts_provider: "openai",
    tts_model: "gpt-4o-mini-tts",
    speakers: [],
  },
  briefing: "",
  audio_file: null,
  audio_url: null,
  transcript: null,
  outline: null,
  job_status: "failed",
  error_message: "generation failed",
};

describe("EpisodeCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    hoisted.resolvePodcastAssetUrlMock.mockResolvedValue(undefined);
    global.URL.createObjectURL = vi.fn(() => "blob:podcast-audio");
    global.URL.revokeObjectURL = hoisted.revokeObjectUrlMock;
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("calls retry handler for failed episode", () => {
    const onRetry = vi.fn();

    render(<EpisodeCard episode={episode} onDelete={vi.fn()} onRetry={onRetry} />);

    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    expect(onRetry).toHaveBeenCalledWith("ep-1");
  });

  it("calls delete handler when delete action is confirmed", () => {
    const onDelete = vi.fn();

    render(<EpisodeCard episode={episode} onDelete={onDelete} />);

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    fireEvent.click(deleteButtons[deleteButtons.length - 1]);

    expect(onDelete).toHaveBeenCalledWith("ep-1");
  });

  it("shows audio fallback error and renders details for completed episodes", async () => {
    hoisted.resolvePodcastAssetUrlMock.mockResolvedValue("https://example.com/audio.mp3");
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
    } as Response);

    render(
      <EpisodeCard
        episode={{
          ...episode,
          id: "ep-2",
          name: "Completed Episode",
          job_status: "completed",
          audio_url: "/api/podcast-audio",
          outline: {
            segments: [{ name: "Intro", description: "Kick-off", size: "short" }],
          },
          transcript: {
            transcript: [{ speaker: "Host", dialogue: "Welcome back" }],
          },
        }}
        onDelete={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(screen.getAllByText(/audio unavailable/i).length).toBeGreaterThan(0);
    });

    expect(screen.queryByRole("button", { name: /retry/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /details/i }));
    expect(screen.getAllByText("Completed Episode").length).toBeGreaterThan(0);
    expect(screen.getByText("Kick-off")).toBeInTheDocument();
    expect(screen.getByText("Welcome back")).toBeInTheDocument();
  });

  it("renders protected audio player on successful fetch and cleans up blob url", async () => {
    hoisted.resolvePodcastAssetUrlMock.mockResolvedValue("https://example.com/audio.mp3");
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(["audio"]),
    } as Response);

    const { unmount } = render(
      <EpisodeCard
        episode={{
          ...episode,
          id: "ep-3",
          name: "Audio Ready",
          job_status: "completed",
          audio_url: "/api/audio-protected",
        }}
        onDelete={vi.fn()}
      />,
    );

    await waitFor(() => {
      const audio = document.querySelector('audio[src="blob:podcast-audio"]');
      expect(audio).not.toBeNull();
    });

    expect(global.fetch).toHaveBeenCalledWith("https://example.com/audio.mp3", {
      headers: {},
    });

    unmount();
    expect(hoisted.revokeObjectUrlMock).toHaveBeenCalledWith("blob:podcast-audio");
  });
});
