"use client";

import { Toaster as Sonner, type ToasterProps } from "sonner";
import { useThemeStore } from "@/lib/stores/theme-store";

const Toaster = ({ ...props }: ToasterProps) => {
  const theme = useThemeStore((state) => state.theme);
  const systemTheme = useThemeStore((state) => state.getSystemTheme());
  const effectiveTheme = theme === "system" ? systemTheme : theme;

  return (
    <Sonner
      theme={effectiveTheme as ToasterProps["theme"]}
      className="toaster group"
      position="bottom-right"
      visibleToasts={1}
      expand={false}
      offset={16}
      toastOptions={{
        duration: 5000,
        classNames: {
          toast: "ui-toast-surface max-w-[280px]",
        },
      }}
      style={
        {
          "--normal-bg": "var(--card)",
          "--normal-text": "var(--foreground)",
          "--normal-border": "var(--border)",
          "--success-bg": "var(--primary)",
          "--success-text": "var(--primary-foreground)",
          "--success-border": "var(--primary)",
        } as React.CSSProperties
      }
      {...props}
    />
  );
};

export { Toaster };
