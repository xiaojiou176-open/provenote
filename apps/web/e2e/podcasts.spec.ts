import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";

const shouldAssertVisualBaseline = process.env.PLAYWRIGHT_DISABLE_VISUAL_BASELINES !== "1";

test("podcasts: visual baseline", async ({ page }) => {
  test.setTimeout(60_000);
  await page.setViewportSize({ width: 1440, height: 900 });

  const speakerProfile = {
    id: "spk-visual",
    name: "Visual Host",
    description: "Host profile for visual baseline",
    tts_provider: "google",
    tts_model: "gemini-2.5-flash-preview-tts",
    speakers: [
      {
        name: "Taylor",
        voice_id: "voice-taylor",
        backstory: "Audio host",
        personality: "Clear and structured",
      },
    ],
  };

  const episodeProfile = {
    id: "epf-visual",
    name: "Visual Brief",
    description: "Visual baseline episode format",
    speaker_config: "Visual Host",
    outline_provider: "google",
    outline_model: "gemini-2.5-flash",
    transcript_provider: "google",
    transcript_model: "gemini-2.5-flash",
    default_briefing: "Summarize in a concise format.",
    num_segments: 3,
  };

  await setupMockApi(page, {
    models: [
      {
        id: "mdl-visual-lang",
        name: "gemini-2.5-flash",
        provider: "google",
        type: "language",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
      {
        id: "mdl-visual-tts",
        name: "gemini-2.5-flash-preview-tts",
        provider: "google",
        type: "text_to_speech",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
    ],
    notebooks: [
      {
        id: "nb-podcast-visual",
        name: "Podcast Visual Notebook",
        description: "Notebook for podcast baseline",
        archived: false,
        source_count: 1,
        note_count: 1,
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
      },
    ],
    speakerProfiles: [speakerProfile],
    episodeProfiles: [episodeProfile],
    podcastEpisodes: [
      {
        id: "ep-visual",
        name: "Visual Episode",
        episode_profile: episodeProfile,
        speaker_profile: speakerProfile,
        briefing: "Visual baseline episode",
        audio_file: null,
        audio_url: null,
        transcript: null,
        outline: null,
        created: "2025-01-03T00:00:00.000Z",
        job_status: "completed",
        error_message: null,
      },
    ],
  });

  await page.goto("/podcasts", { waitUntil: "domcontentloaded" });
  await expect(page).toHaveURL(/\/podcasts$/, { timeout: 15_000 });
  await expect(page.getByRole("heading", { level: 1, name: "Podcasts" })).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByText("Visual Episode")).toBeVisible({ timeout: 15_000 });

  if (shouldAssertVisualBaseline) {
    await expect(page).toHaveScreenshot("podcasts-overview.png", {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.03,
      maxDiffPixels: 17000,
    });
  }
});

test("podcasts: retry, delete, and generate dialog actions", async ({ page }) => {
  test.setTimeout(90_000);
  let episodeListRequests = 0;
  let deleteEpisodeRequests = 0;
  let generateRequests = 0;

  page.on("request", (request) => {
    const url = request.url();

    if (request.method() === "GET" && url.includes("/api/podcasts/episodes")) {
      episodeListRequests += 1;
    }
    if (request.method() === "DELETE" && /\/api\/podcasts\/episodes\/[^/]+$/.test(url)) {
      deleteEpisodeRequests += 1;
    }
    if (request.method() === "POST" && url.includes("/api/podcasts/generate")) {
      generateRequests += 1;
    }
  });

  const speakerProfile = {
    id: "spk-host-duo",
    name: "Host Duo",
    description: "Two host setup",
    tts_provider: "google",
    tts_model: "gemini-2.5-flash-preview-tts",
    speakers: [
      {
        name: "Alex",
        voice_id: "voice-alex",
        backstory: "Technical host",
        personality: "Curious and concise",
      },
    ],
  };

  const episodeProfile = {
    id: "epf-tech-brief",
    name: "Tech Brief",
    description: "Weekly tech recap format",
    speaker_config: "Host Duo",
    outline_provider: "google",
    outline_model: "gemini-2.5-flash",
    transcript_provider: "google",
    transcript_model: "gemini-2.5-flash",
    default_briefing: "Keep it factual and short.",
    num_segments: 4,
  };

  await setupMockApi(page, {
    models: [
      {
        id: "mdl-lang-1",
        name: "gemini-2.5-flash",
        provider: "google",
        type: "language",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
      {
        id: "mdl-tts-1",
        name: "gemini-2.5-flash-preview-tts",
        provider: "google",
        type: "text_to_speech",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
    ],
    notebooks: [
      {
        id: "nb-podcast",
        name: "Podcast Notes",
        description: "Notebook for podcast context",
        archived: false,
        source_count: 2,
        note_count: 2,
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
      },
    ],
    sources: [
      {
        id: "src-podcast-context",
        title: "Podcast Context Source",
        created: "2025-01-02T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
        insights_count: 1,
        embedded: true,
        notebooks: ["nb-podcast"],
        asset: {
          url: "https://example.com/podcast-context",
        },
      },
    ],
    speakerProfiles: [speakerProfile],
    episodeProfiles: [episodeProfile],
    podcastEpisodes: [
      {
        id: "ep-failed",
        name: "Episode With Error",
        episode_profile: episodeProfile,
        speaker_profile: speakerProfile,
        briefing: "Failed briefing",
        audio_file: null,
        audio_url: null,
        transcript: null,
        outline: null,
        created: "2025-01-03T00:00:00.000Z",
        job_status: "failed",
        error_message: "Rate limit exceeded",
      },
    ],
  });

  await page.goto("/podcasts", { waitUntil: "domcontentloaded" });
  await expect(page).toHaveURL(/\/podcasts$/, { timeout: 10_000 });
  await expect.poll(() => episodeListRequests, { timeout: 30_000 }).toBeGreaterThan(0);

  const failedEpisodeCard = page.getByTestId("podcast-episode-card-ep-failed");
  await expect.poll(async () => failedEpisodeCard.count(), { timeout: 30_000 }).toBeGreaterThan(0);
  await expect(failedEpisodeCard).toBeVisible({ timeout: 30_000 });
  await expect(failedEpisodeCard.getByText("Rate limit exceeded")).toBeVisible();

  const retryResponse = page.waitForResponse((response) => {
    return (
      response.request().method() === "POST" &&
      /\/api\/podcasts\/episodes\/[^/]+\/retry$/.test(response.url())
    );
  });
  await failedEpisodeCard.getByRole("button", { name: "Retry" }).click();
  await expect((await retryResponse).status()).toBe(200);
  await expect(failedEpisodeCard.getByText("Rate limit exceeded")).toHaveCount(0);

  await failedEpisodeCard.getByRole("button", { name: "Delete" }).click();
  const deleteDialog = page.getByRole("alertdialog");
  await expect(deleteDialog).toBeVisible();
  await deleteDialog.getByRole("button", { name: "Cancel" }).click();
  await expect(deleteDialog).toHaveCount(0);
  await expect(failedEpisodeCard).toBeVisible();
  expect(deleteEpisodeRequests).toBe(0);

  await failedEpisodeCard.getByRole("button", { name: "Delete" }).click();
  const deleteDialogConfirm = page.getByRole("alertdialog");
  await expect(deleteDialogConfirm).toBeVisible();
  const deleteResponse = page.waitForResponse((response) => {
    return (
      response.request().method() === "DELETE" &&
      /\/api\/podcasts\/episodes\/[^/]+$/.test(response.url())
    );
  });
  await deleteDialogConfirm.getByRole("button", { name: "Delete" }).click();
  await expect((await deleteResponse).status()).toBe(200);
  expect(deleteEpisodeRequests).toBe(1);
  await expect(failedEpisodeCard).toHaveCount(0);

  const generatePodcastButton = page.getByRole("button", { name: "Generate Podcast" });
  await expect(generatePodcastButton).toBeVisible();
  await generatePodcastButton.click();
  const generateDialog = page.getByRole("dialog");
  await expect(
    generateDialog.getByRole("heading", { name: "Generate Podcast Episode" }),
  ).toBeVisible();
  const episodeProfileField = generateDialog.getByLabel("Episode profile");
  await expect(episodeProfileField).toBeVisible();
  await episodeProfileField.click();
  await page.getByRole("option", { name: "Tech Brief" }).click();
  await expect(episodeProfileField).toContainText("Tech Brief");

  const episodeNameField = generateDialog.locator("#episode_name");
  await episodeNameField.fill("Tech Brief E2E Episode");
  await expect(episodeNameField).toHaveValue("Tech Brief E2E Episode");

  const instructionsField = generateDialog.locator("#instructions");
  await instructionsField.fill("Focus on a concise recap and practical outcomes.");
  await expect(instructionsField).toHaveValue("Focus on a concise recap and practical outcomes.");

  const generateActionButton = generateDialog.getByRole("button", { name: /generate/i }).first();
  await expect(generateActionButton).toBeEnabled();
  await page.getByRole("button", { name: "Cancel" }).click();
  await expect(page.getByRole("heading", { name: "Generate Podcast Episode" })).toHaveCount(0);
  expect(generateRequests).toBe(0);

  await page.getByRole("button", { name: "Generate Podcast" }).click();
  const generateDialogSubmit = page.getByRole("dialog");
  await expect(
    generateDialogSubmit.getByRole("heading", { name: "Generate Podcast Episode" }),
  ).toBeVisible();
  await generateDialogSubmit.getByRole("button", { name: /Podcast Notes/i }).click();
  const selectedSourceCheckbox = generateDialogSubmit.locator(
    "#source-selection-src-podcast-context",
  );
  await expect(selectedSourceCheckbox).toBeVisible({ timeout: 20_000 });
  await expect(selectedSourceCheckbox).toHaveAttribute("data-state", "checked");

  const episodeProfileFieldSubmit = generateDialogSubmit.getByLabel("Episode profile");
  await episodeProfileFieldSubmit.click();
  await page.getByRole("option", { name: "Tech Brief" }).click();
  await generateDialogSubmit.locator("#episode_name").fill("Tech Brief E2E Episode Submit");
  await generateDialogSubmit
    .locator("#instructions")
    .fill("Focus on practical outcomes and include the key trade-offs.");

  const generateRequest = page.waitForRequest((request) => {
    return request.method() === "POST" && request.url().includes("/api/podcasts/generate");
  });
  const generateResponse = page.waitForResponse((response) => {
    return (
      response.request().method() === "POST" && response.url().includes("/api/podcasts/generate")
    );
  });
  await generateDialogSubmit
    .getByRole("button", { name: /generate/i })
    .first()
    .click();

  const generatePayload = JSON.parse((await generateRequest).postData() ?? "{}");
  expect(generatePayload).toMatchObject({
    episode_profile: "Tech Brief",
    episode_name: "Tech Brief E2E Episode Submit",
    briefing_suffix: "Focus on practical outcomes and include the key trade-offs.",
  });
  expect(typeof generatePayload.content).toBe("string");
  expect(generatePayload.content).toContain('"sources"');
  await expect((await generateResponse).status()).toBe(200);
  expect(generateRequests).toBe(1);
  await expect(page.getByRole("heading", { name: "Generate Podcast Episode" })).toHaveCount(0, {
    timeout: 10_000,
  });
});
