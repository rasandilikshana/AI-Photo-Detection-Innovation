<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Shield, Trophy, Star, ArrowUpRight, FileImage, Fingerprint, Globe, Link2 } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)

const layers = [
  { icon: FileImage, label: 'Metadata analysis' },
  { icon: Fingerprint, label: 'Sensor fingerprint' },
  { icon: Globe, label: 'AI detection' },
  { icon: Link2, label: 'RAW linkage' },
]

const features = [
  {
    icon: Shield,
    title: 'Forensic verification',
    content: 'Every entry passes layered forensic analysis — metadata, sensor noise, and external AI detection — before it reaches a judge.',
  },
  {
    icon: Trophy,
    title: 'Fair competition',
    content: 'Compete with confidence knowing every submission in the field has been verified as a genuine photograph.',
  },
  {
    icon: Star,
    title: 'Human judging',
    content: 'Verified work is scored by real judges on composition, technical skill, and creativity — never by an algorithm.',
  },
]

const steps = [
  { title: 'Create your account', description: 'Sign up free as a photographer in under a minute' },
  { title: 'Choose a competition', description: 'Browse open competitions and pick one that fits your work' },
  { title: 'Submit JPG + RAW', description: 'Upload both files so verification can link them to your camera' },
  { title: 'Get judged', description: 'Judges score verified entries and winners are announced' },
]
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="container mx-auto px-6 pt-16 md:pt-24 pb-14 text-center">
      <div class="animate-fade-in-up">
        <span class="inline-flex items-center gap-2 rounded-full border bg-card px-4 py-1.5 text-xs md:text-sm font-medium text-muted-foreground">
          <span class="relative flex h-2 w-2">
            <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand opacity-75"></span>
            <span class="relative inline-flex h-2 w-2 rounded-full bg-brand"></span>
          </span>
          AI-verified photography competitions
        </span>
      </div>

      <h1 class="mt-6 text-4xl md:text-6xl lg:text-7xl font-display font-semibold tracking-tight text-balance animate-fade-in-up" style="animation-delay: 80ms">
        <span class="text-muted-foreground">Where</span> authentic photography
        <span class="text-muted-foreground">wins.</span>
      </h1>

      <p class="mx-auto mt-6 max-w-2xl text-base md:text-lg text-muted-foreground leading-relaxed animate-fade-in-up" style="animation-delay: 160ms">
        Every entry passes layered AI forensics before human judges score it.
        Submit genuine photos and compete with photographers worldwide — no AI images, no exceptions.
      </p>

      <div class="mt-8 flex flex-wrap gap-3 justify-center animate-fade-in-up" style="animation-delay: 240ms">
        <Button size="lg" @click="router.push('/competitions')">
          Browse competitions
        </Button>
        <Button v-if="!isAuthenticated" size="lg" variant="outline" @click="router.push('/register')">
          Create account
        </Button>
        <Button v-else size="lg" variant="outline" @click="router.push('/my-submissions')">
          My submissions
        </Button>
      </div>

      <!-- Verification layer chips -->
      <div class="mt-10 flex flex-wrap items-center justify-center gap-2 animate-fade-in-up" style="animation-delay: 320ms">
        <span
          v-for="layer in layers"
          :key="layer.label"
          class="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground"
        >
          <component :is="layer.icon" class="w-3.5 h-3.5" />
          {{ layer.label }}
        </span>
      </div>
    </section>

    <!-- Features -->
    <section class="container mx-auto px-6 py-14">
      <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-10">
        <div>
          <span class="inline-flex items-center rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
            Why A.V.A.R.
          </span>
          <h2 class="mt-4 text-3xl md:text-5xl font-display font-semibold tracking-tight text-balance">
            Built for fair competition
          </h2>
        </div>
        <p class="max-w-sm text-sm md:text-base text-muted-foreground">
          Scientific verification first, expert judgment second — so the best real photograph wins.
        </p>
      </div>

      <div class="grid md:grid-cols-3 gap-5">
        <Card v-for="feature in features" :key="feature.title" class="rounded-2xl p-7 transition-shadow hover:shadow-lg">
          <div class="w-11 h-11 rounded-xl bg-secondary flex items-center justify-center mb-5">
            <component :is="feature.icon" class="w-5 h-5 text-foreground" />
          </div>
          <h3 class="text-lg font-display font-semibold mb-2">{{ feature.title }}</h3>
          <p class="text-sm md:text-base text-muted-foreground leading-relaxed">{{ feature.content }}</p>
        </Card>
      </div>
    </section>

    <!-- How it works -->
    <section class="container mx-auto px-6 py-14">
      <div class="text-center mb-10">
        <span class="inline-flex items-center rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
          How it works
        </span>
        <h2 class="mt-4 text-3xl md:text-5xl font-display font-semibold tracking-tight">
          From upload to verdict
        </h2>
      </div>

      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div
          v-for="(step, index) in steps"
          :key="step.title"
          class="rounded-2xl border bg-card p-6"
        >
          <p class="font-display text-sm font-semibold text-muted-foreground">
            {{ String(index + 1).padStart(2, '0') }}
          </p>
          <div class="mt-4 h-px w-full bg-border" aria-hidden="true"></div>
          <h3 class="mt-4 text-base md:text-lg font-display font-semibold">{{ step.title }}</h3>
          <p class="mt-1.5 text-sm text-muted-foreground leading-relaxed">{{ step.description }}</p>
        </div>
      </div>
    </section>

    <!-- Dark CTA band -->
    <section class="container mx-auto px-6 py-14 pb-20">
      <div class="relative overflow-hidden rounded-3xl bg-ink text-ink-foreground p-8 md:p-14">
        <div
          aria-hidden="true"
          class="pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full bg-brand/20 blur-3xl"
        ></div>
        <div class="relative flex flex-col md:flex-row md:items-center md:justify-between gap-8">
          <div class="max-w-xl">
            <span class="inline-flex items-center gap-2 rounded-full border border-white/15 px-3 py-1 text-xs font-medium text-ink-muted">
              <span class="h-1.5 w-1.5 rounded-full bg-brand"></span>
              Verification included
            </span>
            <h2 class="mt-5 text-3xl md:text-5xl font-display font-semibold tracking-tight text-balance">
              Ready to prove your work is real?
            </h2>
            <p class="mt-4 text-sm md:text-base text-ink-muted leading-relaxed">
              Join photographers competing on craft, not prompts. Create an account,
              pick a competition, and let your genuine work speak.
            </p>
            <div class="mt-7 flex flex-wrap gap-3">
              <Button v-if="!isAuthenticated" size="lg" variant="brand" @click="router.push('/register')">
                Create your account
              </Button>
              <Button v-else size="lg" variant="brand" @click="router.push('/competitions')">
                Enter a competition
              </Button>
              <Button
                size="lg"
                variant="ghost"
                class="text-ink-foreground hover:bg-white/10 hover:text-ink-foreground"
                @click="router.push('/competitions')"
              >
                See competitions
                <ArrowUpRight class="w-4 h-4" />
              </Button>
            </div>
          </div>
          <div class="hidden lg:flex flex-col gap-3" aria-hidden="true">
            <div
              v-for="layer in layers"
              :key="layer.label"
              class="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-5 py-3.5"
            >
              <component :is="layer.icon" class="w-4 h-4 text-brand" />
              <span class="text-sm font-medium">{{ layer.label }}</span>
              <span class="ml-auto text-xs font-semibold text-brand">PASS</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
