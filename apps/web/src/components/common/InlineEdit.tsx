"use client";

import { AlertCircle, CheckCircle2 } from "lucide-react";
import { type RefObject, useEffect, useId, useRef, useState } from "react";
import { useTranslation } from "@/lib/hooks/use-translation";
import { cn } from "@/lib/utils";

interface InlineEditProps {
  value: string;
  onSave: (value: string) => void | Promise<void>;
  className?: string;
  inputClassName?: string;
  placeholder?: string;
  multiline?: boolean;
  emptyText?: string;
  id?: string;
  name?: string;
  autocomplete?: string;
}

export function InlineEdit({
  value,
  onSave,
  className,
  inputClassName,
  placeholder,
  multiline = false,
  emptyText,
  id: providedId,
  name,
  autocomplete = "off",
}: InlineEditProps) {
  const generatedId = useId();
  const id = providedId || generatedId;
  const { t } = useTranslation();
  const defaultEmptyText = emptyText || t.common.clickToEdit;
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [isSaving, setIsSaving] = useState(false);
  const [saveState, setSaveState] = useState<"idle" | "success" | "error">("idle");
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  useEffect(() => {
    setEditValue(value);
  }, [value]);

  useEffect(() => {
    if (saveState === "idle") {
      return;
    }
    const timer = window.setTimeout(() => setSaveState("idle"), 2200);
    return () => window.clearTimeout(timer);
  }, [saveState]);

  const handleSave = async () => {
    if (editValue.trim() === value.trim()) {
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    setSaveState("idle");
    try {
      await onSave(editValue.trim());
      setIsEditing(false);
      setSaveState("success");
    } catch {
      // Reset on error
      setEditValue(value);
      setSaveState("error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
    setSaveState("idle");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !multiline) {
      e.preventDefault();
      handleSave();
    } else if (e.key === "Escape") {
      e.preventDefault();
      handleCancel();
    }
  };

  if (!isEditing) {
    return (
      <button
        type="button"
        className={cn(
          "cursor-pointer hover:bg-muted/50 rounded px-2 py-1 -mx-2 -my-1 transition-colors text-left w-full break-all",
          className,
        )}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsEditing(true);
        }}
      >
        {value || <span className="text-muted-foreground">{defaultEmptyText}</span>}
      </button>
    );
  }

  if (multiline) {
    return (
      <div className="space-y-1">
        <textarea
          ref={inputRef as RefObject<HTMLTextAreaElement>}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => {
            if (!isSaving && editValue.trim() !== value.trim()) {
              handleSave();
            } else if (editValue.trim() === value.trim()) {
              setIsEditing(false);
            }
          }}
          className={cn(
            "px-2 py-1 bg-background border rounded focus:outline-none focus:ring-2 focus:ring-primary w-full transition-[box-shadow,border-color,background-color] duration-150",
            "min-h-[60px] resize-none",
            inputClassName,
          )}
          placeholder={placeholder}
          disabled={isSaving}
          aria-busy={isSaving}
          aria-invalid={saveState === "error"}
          id={id}
          name={name}
          autoComplete={autocomplete}
        />
        <div className="min-h-4 text-xs" aria-live="polite">
          {saveState === "success" && (
            <span className="ui-success-pop inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {t.common.saveSuccess}
            </span>
          )}
          {saveState === "error" && (
            <span className="inline-flex items-center gap-1 text-destructive ui-form-error">
              <AlertCircle className="h-3.5 w-3.5" />
              {t.common.error}
            </span>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <input
        ref={inputRef as RefObject<HTMLInputElement>}
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => {
          if (!isSaving && editValue.trim() !== value.trim()) {
            handleSave();
          } else if (editValue.trim() === value.trim()) {
            setIsEditing(false);
          }
        }}
        className={cn(
          "px-2 py-1 bg-background border rounded focus:outline-none focus:ring-2 focus:ring-primary w-full transition-[box-shadow,border-color,background-color] duration-150",
          inputClassName,
        )}
        placeholder={placeholder}
        disabled={isSaving}
        aria-busy={isSaving}
        aria-invalid={saveState === "error"}
        id={id}
        name={name}
        autoComplete={autocomplete}
      />
      <div className="min-h-4 text-xs" aria-live="polite">
        {saveState === "success" && (
          <span className="ui-success-pop inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" />
            {t.common.saveSuccess}
          </span>
        )}
        {saveState === "error" && (
          <span className="inline-flex items-center gap-1 text-destructive ui-form-error">
            <AlertCircle className="h-3.5 w-3.5" />
            {t.common.error}
          </span>
        )}
      </div>
    </div>
  );
}
