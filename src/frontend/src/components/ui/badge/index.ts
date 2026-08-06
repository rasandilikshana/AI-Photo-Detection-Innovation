import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Badge } from "./Badge.vue"

export const badgeVariants = cva(
  "inline-flex gap-1 items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        // Default: ink solid
        default:
          "border-transparent bg-primary text-primary-foreground",
        // Secondary: muted
        secondary:
          "border-transparent bg-secondary text-secondary-foreground",
        // Destructive
        destructive:
          "border-transparent bg-destructive text-destructive-foreground",
        // Outline
        outline:
          "border-border bg-transparent text-foreground",
        // Brand: vivid verified-green
        brand:
          "border-transparent bg-brand text-brand-foreground",
        // Success
        success:
          "border-transparent bg-success text-success-foreground",
        // Warning
        warning:
          "border-transparent bg-warning text-warning-foreground",
        // Info
        info:
          "border-transparent bg-info text-info-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
)

export type BadgeVariants = VariantProps<typeof badgeVariants>
