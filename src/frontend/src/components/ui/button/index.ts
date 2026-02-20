import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Button } from "./Button.vue"

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Primary: Solid with subtle hover
        default:
          "bg-primary text-primary-foreground hover:bg-primary/90 active:scale-[0.98]",
        // Destructive
        destructive:
          "bg-red-600 text-white hover:bg-red-700",
        // Outline: Clean border
        outline:
          "border border-border bg-transparent hover:bg-accent hover:text-accent-foreground",
        // Secondary
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        // Ghost
        ghost:
          "hover:bg-accent hover:text-accent-foreground",
        // Link
        link:
          "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-lg px-8",
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
