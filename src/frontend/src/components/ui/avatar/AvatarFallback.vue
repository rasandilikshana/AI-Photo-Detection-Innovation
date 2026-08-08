<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import type { AvatarFallbackProps } from "reka-ui"
import { reactiveOmit } from "@vueuse/core"
import { AvatarFallback } from "reka-ui"
import { cn } from "@/lib/utils"

const props = defineProps<AvatarFallbackProps & { class?: HTMLAttributes["class"] }>()

const delegatedProps = reactiveOmit(props, "class")
</script>

<template>
  <AvatarFallback
    v-bind="delegatedProps"
    :class="cn('flex h-full w-full items-center justify-center rounded-[inherit]', props.class)"
  >
    <slot />
  </AvatarFallback>
</template>
