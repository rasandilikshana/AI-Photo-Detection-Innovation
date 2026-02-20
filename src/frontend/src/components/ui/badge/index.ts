import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Badge } from "./Badge.vue"

export const badgeVariants = cva(
  "inline-flex gap-1 items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        // Default: Primary solid
        default:
          "border-transparent bg-primary text-primary-foreground",
        // Secondary: Muted
        secondary:
          "border-transparent bg-secondary text-secondary-foreground",
        // Destructive
        destructive:
          "border-transparent bg-red-600 text-white",
        // Outline
        outline:
          "border-border bg-transparent text-foreground",
        // Success: Green
        success:
          "border-transparent bg-emerald-600 text-white",
        // Warning: Amber
        warning:
          "border-transparent bg-amber-600 text-white",
        // Info: Blue
        info:
          "border-transparent bg-sky-600 text-white",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
)

export type BadgeVariants = VariantProps<typeof badgeVariants>
