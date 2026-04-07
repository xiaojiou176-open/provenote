import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TemplatesTab } from "./TemplatesTab";

const hoisted = vi.hoisted(() => ({
  useEpisodeProfilesMock: vi.fn(),
  useSpeakerProfilesMock: vi.fn(),
  useModelsMock: vi.fn(),
}));

vi.mock("@/lib/hooks/use-podcasts", () => ({
  useEpisodeProfiles: () => hoisted.useEpisodeProfilesMock(),
  useSpeakerProfiles: (episodeProfiles: unknown) => hoisted.useSpeakerProfilesMock(episodeProfiles),
}));

vi.mock("@/lib/hooks/use-models", () => ({
  useModels: () => hoisted.useModelsMock(),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      podcasts: {
        templatesWorkspaceTitle: "Templates workspace",
        templatesWorkspaceDesc: "Manage episode and speaker templates",
        howTemplatesPowerTitle: "How templates power podcasts",
        howTemplatesPowerDesc: "Templates help structure episodes",
        episodeProfilesSetFormat: "Episode profiles set format",
        episodeProfilesList1: "Episode list 1",
        episodeProfilesList2: "Episode list 2",
        episodeProfilesList3: "Episode list 3",
        speakerProfilesBringVoices: "Speaker profiles bring voices",
        speakerProfilesList1: "Speaker list 1",
        speakerProfilesList2: "Speaker list 2",
        speakerProfilesList3: "Speaker list 3",
        recommendedWorkflow: "Recommended workflow",
        workflowStep1: "Workflow 1",
        workflowStep2: "Workflow 2",
        workflowStep3: "Workflow 3",
        workflowHint: "Workflow hint",
        failedToLoadTemplates: "Failed to load templates",
        failedToLoadTemplatesDesc: "Template request failed",
        loadingTemplates: "Loading templates",
      },
    },
  }),
}));

vi.mock("@/components/podcasts/EpisodeProfilesPanel", () => ({
  EpisodeProfilesPanel: ({ episodeProfiles }: { episodeProfiles: Array<{ id: string }> }) => (
    <div data-testid="episode-profiles-panel">
      {episodeProfiles.map((item) => item.id).join(",")}
    </div>
  ),
}));

vi.mock("@/components/podcasts/SpeakerProfilesPanel", () => ({
  SpeakerProfilesPanel: ({
    speakerProfiles,
    usage,
  }: {
    speakerProfiles: Array<{ id: string }>;
    usage: Record<string, number>;
  }) => (
    <div data-testid="speaker-profiles-panel">
      {speakerProfiles.map((item) => item.id).join(",")}::{Object.keys(usage).length}
    </div>
  ),
}));

vi.mock("@/components/ui/accordion", () => ({
  Accordion: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AccordionItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AccordionTrigger: ({ children }: { children: ReactNode }) => (
    <button type="button">{children}</button>
  ),
  AccordionContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

describe("TemplatesTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state while templates and models are loading", () => {
    hoisted.useEpisodeProfilesMock.mockReturnValue({
      episodeProfiles: [],
      isLoading: true,
      error: null,
    });
    hoisted.useSpeakerProfilesMock.mockReturnValue({
      speakerProfiles: [],
      usage: {},
      isLoading: true,
      error: null,
    });
    hoisted.useModelsMock.mockReturnValue({
      data: [],
      isLoading: true,
      error: null,
    });

    render(<TemplatesTab />);

    expect(screen.getByText("Loading templates")).toBeInTheDocument();
  });

  it("shows destructive alert on load failure and renders panels on success", () => {
    hoisted.useEpisodeProfilesMock.mockReturnValue({
      episodeProfiles: [{ id: "ep-profile-1" }],
      isLoading: false,
      error: null,
    });
    hoisted.useSpeakerProfilesMock.mockReturnValue({
      speakerProfiles: [{ id: "speaker-1" }],
      usage: { "speaker-1": 1 },
      isLoading: false,
      error: null,
    });
    hoisted.useModelsMock.mockReturnValue({
      data: [
        { id: "lang-1", name: "Gemini", type: "language", provider: "google" },
        { id: "tts-1", name: "Voice", type: "text_to_speech", provider: "google" },
      ],
      isLoading: false,
      error: new Error("boom"),
    });

    render(<TemplatesTab />);

    expect(screen.getByText("Failed to load templates")).toBeInTheDocument();
    expect(screen.getByTestId("episode-profiles-panel")).toHaveTextContent("ep-profile-1");
    expect(screen.getByTestId("speaker-profiles-panel")).toHaveTextContent("speaker-1::1");

    fireEvent.click(screen.getByRole("button", { name: /How templates power podcasts/i }));
    expect(screen.getByText("Templates help structure episodes")).toBeInTheDocument();
  });
});
