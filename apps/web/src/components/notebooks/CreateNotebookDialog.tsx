"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useCreateNotebook } from "@/lib/hooks/use-notebooks";
import { useTranslation } from "@/lib/hooks/use-translation";

const createNotebookSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
});

type CreateNotebookFormData = z.infer<typeof createNotebookSchema>;

interface CreateNotebookDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateNotebookDialog({ open, onOpenChange }: CreateNotebookDialogProps) {
  const { t } = useTranslation();
  const createNotebook = useCreateNotebook();
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset,
  } = useForm<CreateNotebookFormData>({
    resolver: zodResolver(createNotebookSchema),
    mode: "onChange",
    defaultValues: {
      name: "",
      description: "",
    },
  });

  const closeDialog = () => onOpenChange(false);

  const onSubmit = async (data: CreateNotebookFormData) => {
    await createNotebook.mutateAsync(data);
    closeDialog();
    reset();
  };

  useEffect(() => {
    if (!open) {
      reset();
    }
  }, [open, reset]);

  const nameErrorId = "notebook-name-error";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="ui-dialog-surface sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>{t.notebooks.createNew}</DialogTitle>
          <DialogDescription>{t.notebooks.createNewDesc}</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="notebook-name">{t.common.name} *</Label>
            <Input
              id="notebook-name"
              {...register("name")}
              className="ui-search-field"
              placeholder={t.notebooks.namePlaceholder}
              autoComplete="off"
              aria-invalid={errors.name ? "true" : "false"}
              aria-describedby={errors.name ? nameErrorId : undefined}
            />
            {errors.name && (
              <p id={nameErrorId} className="ui-form-error text-sm text-destructive">
                {errors.name.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="notebook-description">{t.common.description}</Label>
            <Textarea
              id="notebook-description"
              {...register("description")}
              className="ui-search-field"
              placeholder={t.notebooks.descPlaceholder}
              rows={4}
            />
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              className="ui-icon-button"
              onClick={closeDialog}
            >
              {t.common.cancel}
            </Button>
            <Button
              type="submit"
              className="ui-primary-cta"
              disabled={!isValid || createNotebook.isPending}
            >
              {createNotebook.isPending ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" label={t.common.creating} />
                  {t.common.creating}
                </>
              ) : (
                t.notebooks.createNew
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
