import {
  type UseMutationOptions,
  type UseMutationResult,
  useMutation,
} from "@tanstack/react-query";
import { useToast } from "@/lib/hooks/use-toast";

type MutationToast = {
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
};

type ToastFactory<TArgs extends unknown[]> =
  | MutationToast
  | ((...args: TArgs) => MutationToast | null | undefined);

function resolveToast<TArgs extends unknown[]>(
  toastConfig: ToastFactory<TArgs> | undefined,
  ...args: TArgs
): MutationToast | null | undefined {
  if (!toastConfig) {
    return undefined;
  }
  return typeof toastConfig === "function" ? toastConfig(...args) : toastConfig;
}

type AppMutationOptions<TData, TVariables, TContext> = Omit<
  UseMutationOptions<TData, unknown, TVariables, TContext>,
  "mutationFn" | "onSuccess" | "onError"
> & {
  mutationFn: NonNullable<UseMutationOptions<TData, unknown, TVariables, TContext>["mutationFn"]>;
  onSuccess?: UseMutationOptions<TData, unknown, TVariables, TContext>["onSuccess"];
  onError?: UseMutationOptions<TData, unknown, TVariables, TContext>["onError"];
  successToast?: ToastFactory<[TData, TVariables]>;
  errorToast?: ToastFactory<[unknown, TVariables]>;
};

export function useAppMutation<TData = unknown, TVariables = void, TContext = unknown>(
  options: AppMutationOptions<TData, TVariables, TContext>,
): UseMutationResult<TData, unknown, TVariables, TContext> {
  const { toast } = useToast();
  const { mutationFn, onSuccess, onError, successToast, errorToast, ...mutationOptions } = options;

  return useMutation<TData, unknown, TVariables, TContext>({
    ...mutationOptions,
    mutationFn,
    onSuccess: async (data: TData, variables: TVariables, mutationContext: TContext) => {
      await onSuccess?.(data, variables, mutationContext);

      const payload = resolveToast(successToast, data, variables);
      if (payload) {
        toast(payload);
      }
    },
    onError: async (
      error: unknown,
      variables: TVariables,
      mutationContext: TContext | undefined,
    ) => {
      await onError?.(error, variables, mutationContext);

      const payload = resolveToast(errorToast, error, variables);
      if (payload) {
        toast(payload);
      }
    },
  });
}
