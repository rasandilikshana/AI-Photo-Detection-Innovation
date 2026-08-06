import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Button } from "./Button.vue"

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium ring-offset-background transition-all duration-200 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Primary: ink pill
        default:
          "bg-primary text-primary-foreground hover:bg-primary/85 active:scale-[0.98]",
        // Brand: vivid verified-green pill (use sparingly)
        brand:
          "bg-brand text-brand-foreground hover:bg-brand/85 active:scale-[0.98]",
        // Destructive
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        // Outline: clean hairline pill
        outline:
          "border border-input bg-card hover:bg-accent hover:text-accent-foreground",
        // Secondary
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        // Ghost
        ghost:
          "hover:bg-accent hover:text-accent-foreground",
        // Link
        link:
          "text-foreground underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-9 px-4",
        lg: "h-12 px-7 text-base",
        icon: "h-10 w-10",
        "icon-sm": "size-9",
        "icon-lg": "size-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>
