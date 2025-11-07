# Vue 3 + Vite + Tailwind CSS + shadcn-vue

This is a modern Vue 3 frontend application built with:

- **Vue 3** - Progressive JavaScript framework
- **Vite** - Next generation frontend tooling
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn-vue** - Re-usable components built with Radix Vue and Tailwind CSS
- **Vue Router** - Official router for Vue.js

## Getting Started

### Install dependencies

```bash
pnpm install
```

### Run development server

```bash
pnpm dev
```

The application will be available at `http://localhost:5173`

### Build for production

```bash
pnpm build
```

### Preview production build

```bash
pnpm preview
```

## Project Structure

```
src/
├── components/     # Reusable components
│   └── ui/        # shadcn-vue components
├── views/         # Page components
├── lib/           # Utility functions
├── App.vue        # Root component
├── main.ts        # Application entry point
└── style.css      # Global styles with Tailwind directives
```

## Adding shadcn-vue Components

To add shadcn-vue components, you can use the CLI:

```bash
pnpm dlx shadcn-vue@latest add button
```

This will add the button component to `src/components/ui/button/`

Available components: https://www.shadcn-vue.com/docs/components

## Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [shadcn-vue Documentation](https://www.shadcn-vue.com/)
- [Radix Vue Documentation](https://www.radix-vue.com/)
