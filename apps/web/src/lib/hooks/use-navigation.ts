import { useTranslation } from "@/lib/hooks/use-translation";
import { useNavigationStore } from "@/lib/stores/navigation-store";

export function useNavigation() {
  const store = useNavigationStore();
  const { t } = useTranslation();

  return {
    setReturnTo: store.setReturnTo,
    clearReturnTo: store.clearReturnTo,
    getReturnPath: store.getReturnPath,
    getReturnLabel: (fallbackLabel?: string) =>
      store.getReturnLabel(fallbackLabel || t.common.backToSources),
    returnTo: store.returnTo,
  };
}
