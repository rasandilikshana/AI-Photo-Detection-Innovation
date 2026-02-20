<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Shield, Trophy, Star, UserPlus, Search, Upload, Award } from 'lucide-vue-next'

const router = useRouter()

const features = [
  {
    icon: Shield,
    title: 'AI Detection',
    content: 'Advanced forensic analysis ensures only authentic photographs are accepted in competitions.',
  },
  {
    icon: Trophy,
    title: 'Fair Competition',
    content: 'Compete with confidence knowing all submissions are verified for authenticity.',
  },
  {
    icon: Star,
    title: 'Professional Judging',
    content: 'Your work is evaluated by experienced photographers and industry professionals.',
  },
]

const steps = [
  { icon: UserPlus, title: 'Sign Up', description: 'Create your account and complete your profile' },
  { icon: Search, title: 'Choose Competition', description: 'Browse active competitions and find one that interests you' },
  { icon: Upload, title: 'Submit Photos', description: 'Upload your JPG and RAW files for verification' },
  { icon: Award, title: 'Get Judged', description: 'Professionals evaluate your work and winners are announced' },
]
</script>

<template>
  <div class="container mx-auto px-6 py-16">
    <!-- Hero Section -->
    <div class="text-center space-y-6 mb-20">
      <h1 class="text-5xl md:text-6xl font-bold tracking-tight text-foreground">
        A.V.A.R.
      </h1>
      <p class="text-xl text-muted-foreground">
        Anti-AI Verification and Adjudication Registry
      </p>
      <p class="text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed">
        Join authentic photography competitions with AI-powered verification.
        Submit your genuine photos and compete with photographers worldwide.
      </p>
      <div class="flex gap-4 justify-center pt-6">
        <Button size="lg" class="text-base px-8 py-6" @click="router.push('/competitions')">
          Browse Competitions
        </Button>
        <Button size="lg" variant="outline" class="text-base px-8 py-6" @click="router.push('/register')">
          Get Started
        </Button>
      </div>
    </div>

    <!-- Features Section -->
    <div class="grid md:grid-cols-3 gap-8 mb-20">
      <Card v-for="feature in features" :key="feature.title" class="p-8">
        <div class="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-6">
          <component :is="feature.icon" class="w-7 h-7 text-primary" />
        </div>
        <h3 class="text-xl font-semibold mb-3">{{ feature.title }}</h3>
        <p class="text-base text-muted-foreground leading-relaxed">{{ feature.content }}</p>
      </Card>
    </div>

    <!-- How It Works -->
    <div class="mb-20">
      <h2 class="text-3xl font-bold text-center mb-12">How It Works</h2>
      <div class="grid md:grid-cols-4 gap-8">
        <div v-for="(step, index) in steps" :key="step.title" class="text-center">
          <div class="w-14 h-14 rounded-full bg-primary text-primary-foreground flex items-center justify-center mx-auto mb-4 text-xl font-semibold">
            {{ index + 1 }}
          </div>
          <h3 class="text-lg font-semibold mb-2">{{ step.title }}</h3>
          <p class="text-base text-muted-foreground">{{ step.description }}</p>
        </div>
      </div>
    </div>

    <!-- CTA Section -->
    <Card class="text-center p-12">
      <h2 class="text-2xl font-bold mb-4">
        Ready to showcase your photography?
      </h2>
      <p class="text-lg text-muted-foreground mb-8">
        Join photographers in authentic competitions
      </p>
      <Button size="lg" class="text-base px-8 py-6" @click="router.push('/register')">
        Create Your Account
      </Button>
    </Card>
  </div>
</template>
