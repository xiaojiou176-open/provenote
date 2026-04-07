"use client";

import { useEffect, useMemo, useState } from "react";
import { NoteEditorDialog } from "@/components/notebooks/NoteEditorDialog";
import { SourceDialog } from "@/components/source/SourceDialog";
import { SourceInsightDialog } from "@/components/source/SourceInsightDialog";
import { useModalManager } from "@/lib/hooks/use-modal-manager";

/**
 * Modal Provider Component
 *
 * Renders modals based on URL query parameters (?modal=type&id=xxx)
 * Manages modal state through the useModalManager hook
 *
 * Supported modal types:
 * - source: Source detail modal
 * - note: Note editor modal
 * - insight: Source insight modal
 */
export function ModalProvider() {
  const { modalType, modalId, closeModal } = useModalManager();
  const [dismissedModalKey, setDismissedModalKey] = useState<string | null>(null);
  const activeModalKey = useMemo(
    () => (modalType && modalId ? `${modalType}:${modalId}` : null),
    [modalId, modalType],
  );

  useEffect(() => {
    if (!activeModalKey || dismissedModalKey !== activeModalKey) {
      setDismissedModalKey(null);
    }
  }, [activeModalKey, dismissedModalKey]);

  const handleModalOpenChange = (open: boolean) => {
    if (open) {
      return;
    }
    if (activeModalKey) {
      setDismissedModalKey(activeModalKey);
    }
    closeModal();
  };

  const isModalVisible = (type: "source" | "note" | "insight") =>
    modalType === type && activeModalKey !== dismissedModalKey;

  return (
    <>
      {/* Source Modal */}
      <SourceDialog
        open={isModalVisible("source")}
        onOpenChange={handleModalOpenChange}
        sourceId={modalId}
      />

      {/* Note Modal */}
      <NoteEditorDialog
        open={isModalVisible("note")}
        onOpenChange={handleModalOpenChange}
        notebookId="" // Will need to be fetched or handled in Phase 9
        note={modalId ? { id: modalId, title: null, content: null } : undefined}
      />

      {/* Source Insight Modal */}
      <SourceInsightDialog
        open={isModalVisible("insight")}
        onOpenChange={handleModalOpenChange}
        insight={modalId ? { id: modalId, insight_type: "", content: "" } : undefined}
      />
    </>
  );
}
