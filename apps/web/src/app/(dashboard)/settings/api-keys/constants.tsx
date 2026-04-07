import { Code, MessageSquare, Mic, Volume2 } from "lucide-react";
import type { ReactNode } from "react";

export type ModelType = "language" | "embedding" | "text_to_speech" | "speech_to_text";

export const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  google: "Google AI",
};

export const ALL_PROVIDERS = ["google"];

export const PROVIDER_MODALITIES: Record<string, ModelType[]> = {
  google: ["language", "embedding", "text_to_speech", "speech_to_text"],
};

export const PROVIDER_DOCS: Record<string, string> = {
  google: "https://aistudio.google.com/app/apikey",
};

export const TYPE_ICONS: Record<ModelType, ReactNode> = {
  language: <MessageSquare className="h-3 w-3" />,
  embedding: <Code className="h-3 w-3" />,
  text_to_speech: <Volume2 className="h-3 w-3" />,
  speech_to_text: <Mic className="h-3 w-3" />,
};

export const TYPE_COLORS: Record<ModelType, string> = {
  language: "bg-primary/10 text-primary border-primary/20",
  embedding: "bg-secondary text-secondary-foreground border-border",
  text_to_speech: "bg-accent text-accent-foreground border-border",
  speech_to_text: "bg-muted text-foreground border-border",
};

export const TYPE_COLOR_INACTIVE = "bg-muted text-muted-foreground border-border";

export const TYPE_LABELS: Record<ModelType, string> = {
  language: "Language",
  embedding: "Embedding",
  text_to_speech: "TTS",
  speech_to_text: "STT",
};
