import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EpisodesTab } from "./EpisodesTab";

const hoisted = vi.hoisted(() => ({
  usePodcastEpisodesMock: vi.fn(),
  useDeletePodcastEpisodeMock: vi.fn(),
  useRetryPodcastEpisodeMock: vi.fn(),
  deleteMutateAsync: vi.fn(),
  retryMutateAsync: vi.fn(),
  refetchMock: vi.fn(),
}));

vi.mock("@/lib/hooks/use-podcasts", () => ({
  usePodcastEpisodes: hoisted.usePodcastEpisodesMock,
  useDeletePodcastEpisode: hoisted.useDeletePodcastEpisodeMock,
  useRetryPodcastEpisode: hoisted.useRetryPodcastEpisodeMock,
}));

vi.mock("@/components/podcasts/EpisodeCard", () => ({
  EpisodeCard: ({
    episode,
    onDelete,
    onRetry,
  }: {
    episode: { id: string; name: string };
    onDelete: (id: string) => Promise<void>;
    onRetry?: (id: string) => Promise<void>;
  }) => (
    <div data-testid={`episode-${episode.id}`}>
      <span>{episode.name}</span>
      <button type="button" onClick={() => void onDelete(episode.id)}>
        Delete {episode.id}
      </button>
      <button type="button" onClick={() => onRetry && void onRetry(episode.id)}>
        Retry {episode.id}
      </button>
    </div>
  ),
}));

vi.mock("@/components/podcasts/GeneratePodcastDialog", () => ({
  GeneratePodcastDialog: ({ open }: { open: boolean }) => (
    <div data-testid="generate-podcast-dialog">{open ? "open" : "closed"}</div>
  ),
}));

vi.mock("@/components/ui/separator", () => ({
  Separator: () => <hr />,
}));

describe("EpisodesTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.refetchMock.mockResolvedValue(undefined);

    const episode = {
      id: "ep-1",
      name: "Episode One",
      episode_profile: {
        id: "profile-1",
        name: "Interview",
      },
      speaker_profile: {
        id: "speaker-1",
        name: "Host",
        speakers: [],
      },
      briefing: "",
      job_status: "failed",
    };

    hoisted.usePodcastEpisodesMock.mockReturnValue({
      episodes: [episode],
      statusGroups: {
        running: [],
        pending: [],
        completed: [],
        failed: [episode],
      },
      statusCounts: {
        total: 1,
        running: 0,
        completed: 0,
        failed: 1,
        pending: 0,
      },
      isLoading: false,
      isError: false,
      isFetching: false,
      refetch: hoisted.refetchMock,
    });

    hoisted.useDeletePodcastEpisodeMock.mockReturnValue({
      mutateAsync: hoisted.deleteMutateAsync,
      isPending: false,
    });

    hoisted.useRetryPodcastEpisodeMock.mockReturnValue({
      mutateAsync: hoisted.retryMutateAsync,
      isPending: false,
    });

    hoisted.deleteMutateAsync.mockResolvedValue(undefined);
    hoisted.retryMutateAsync.mockResolvedValue(undefined);
  });

  it("refreshes list and opens generate dialog", async () => {
    render(<EpisodesTab />);

    expect(screen.getByTestId("generate-podcast-dialog")).toHaveTextContent("closed");

    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));
    fireEvent.click(screen.getByRole("button", { name: /generate/i }));

    await waitFor(() => {
      expect(hoisted.refetchMock).toHaveBeenCalled();
      expect(screen.getByTestId("generate-podcast-dialog")).toHaveTextContent("open");
    });
  });

  it("routes delete and retry actions to mutations", async () => {
    render(<EpisodesTab />);

    fireEvent.click(screen.getByRole("button", { name: "Delete ep-1" }));
    fireEvent.click(screen.getByRole("button", { name: "Retry ep-1" }));

    await waitFor(() => {
      expect(hoisted.deleteMutateAsync).toHaveBeenCalledWith("ep-1");
      expect(hoisted.retryMutateAsync).toHaveBeenCalledWith("ep-1");
    });
  });
});
