"use client";

import { ExternalLink, Link as LinkIcon, Play } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TabsContent } from "@/components/ui/tabs";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { SourceDetailResponse } from "@/lib/types/api";

interface SourceContentTabProps {
  source: SourceDetailResponse;
  isYouTubeUrl: boolean;
  youTubeVideoId: string | null;
}

export function SourceContentTab({ source, isYouTubeUrl, youTubeVideoId }: SourceContentTabProps) {
  const { t } = useTranslation();

  return (
    <TabsContent value="content" className="mt-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {isYouTubeUrl && <Play className="h-5 w-5" />}
            {t.sources.content}
          </CardTitle>
          {source.asset?.url && !isYouTubeUrl && (
            <CardDescription className="flex items-center gap-2">
              <LinkIcon className="h-4 w-4" />
              <a
                href={source.asset.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline text-primary"
              >
                {source.asset.url}
              </a>
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {isYouTubeUrl && youTubeVideoId && (
            <div className="mb-6">
              <div className="aspect-video rounded-lg overflow-hidden bg-black">
                <iframe
                  src={`https://www.youtube.com/embed/${youTubeVideoId}`}
                  title={t.common.accessibility.ytVideo}
                  className="w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
              {source.asset?.url && (
                <div className="mt-2">
                  <a
                    href={source.asset.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                  >
                    <ExternalLink className="h-3 w-3" />
                    {t.sources.openOnYoutube}
                  </a>
                </div>
              )}
            </div>
          )}
          <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none prose-headings:font-semibold prose-a:text-primary prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-p:mb-4 prose-p:leading-7 prose-li:mb-2">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-4">{children}</p>,
                h1: ({ children }) => <h1 className="text-2xl font-bold mt-6 mb-4">{children}</h1>,
                h2: ({ children }) => <h2 className="text-xl font-bold mt-5 mb-3">{children}</h2>,
                h3: ({ children }) => (
                  <h3 className="text-lg font-semibold mt-4 mb-2">{children}</h3>
                ),
                ul: ({ children }) => <ul className="mb-4 list-disc pl-6">{children}</ul>,
                ol: ({ children }) => <ol className="mb-4 list-decimal pl-6">{children}</ol>,
                li: ({ children }) => <li className="mb-1">{children}</li>,
                table: ({ children }) => (
                  <div className="my-4 overflow-x-auto">
                    <table className="min-w-full border-collapse border border-border">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
                tbody: ({ children }) => <tbody>{children}</tbody>,
                tr: ({ children }) => <tr className="border-b border-border">{children}</tr>,
                th: ({ children }) => (
                  <th className="border border-border px-3 py-2 text-left font-semibold">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="border border-border px-3 py-2">{children}</td>
                ),
              }}
            >
              {source.full_text || t.sources.noContent}
            </ReactMarkdown>
          </div>
        </CardContent>
      </Card>
    </TabsContent>
  );
}
