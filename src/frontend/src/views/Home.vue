<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const router = useRouter()
</script>

<template>
  <div class="container mx-auto px-4 py-12">
    <!-- Hero Section -->
    <div class="text-center space-y-6 mb-16">
      <h1 class="text-5xl font-bold tracking-tight">
        A.V.A.R.
      </h1>
      <p class="text-xl text-muted-foreground max-w-2xl mx-auto">
        Anti-AI Verification and Adjudication Registry
      </p>
      <p class="text-lg text-muted-foreground max-w-3xl mx-auto">
        Join authentic photography competitions with AI-powered verification.
        Submit your genuine photos and compete with photographers worldwide.
      </p>
      <div class="flex gap-4 justify-center mt-8">
        <Button size="lg" @click="router.push('/competitions')">
          Browse Competitions
        </Button>
        <Button size="lg" variant="outline" @click="router.push('/register')">
          Get Started
        </Button>
      </div>
    </div>

    <!-- Features Section -->
    <div class="grid md:grid-cols-3 gap-6 mt-16">
      <Card>
        <CardHeader>
          <CardTitle>AI Detection</CardTitle>
          <CardDescription>Multi-layered AI verification</CardDescription>
        </CardHeader>
        <CardContent>
          Advanced forensic analysis ensures only authentic photographs are accepted in competitions.
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Fair Competition</CardTitle>
          <CardDescription>Level playing field for all</CardDescription>
        </CardHeader>
        <CardContent>
          Compete with confidence knowing all submissions are verified for authenticity.
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Professional Judging</CardTitle>
          <CardDescription>Expert evaluation</CardDescription>
        </CardHeader>
        <CardContent>
          Your work is evaluated by experienced photographers and industry professionals.
        </CardContent>
      </Card>
    </div>

    <!-- How It Works -->
    <div class="mt-20 text-center space-y-8">
      <h2 class="text-3xl font-bold">How It Works</h2>
      <div class="grid md:grid-cols-4 gap-6 mt-8">
        <div class="space-y-4">
          <div class="w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold mx-auto">
            1
          </div>
          <h3 class="font-semibold">Sign Up</h3>
          <p class="text-sm text-muted-foreground">Create your account and complete your profile</p>
        </div>

        <div class="space-y-4">
          <div class="w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold mx-auto">
            2
          </div>
          <h3 class="font-semibold">Choose Competition</h3>
          <p class="text-sm text-muted-foreground">Browse active competitions and find one that interests you</p>
        </div>

        <div class="space-y-4">
          <div class="w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold mx-auto">
            3
          </div>
          <h3 class="font-semibold">Submit Photos</h3>
          <p class="text-sm text-muted-foreground">Upload your JPG and RAW files for verification</p>
        </div>

        <div class="space-y-4">
          <div class="w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold mx-auto">
            4
          </div>
          <h3 class="font-semibold">Get Judged</h3>
          <p class="text-sm text-muted-foreground">Professionals evaluate your work and winners are announced</p>
        </div>
      </div>
    </div>

    <!-- CTA Section -->
    <div class="mt-20 text-center bg-muted rounded-lg p-12">
      <h2 class="text-3xl font-bold mb-4">Ready to showcase your authentic photography?</h2>
      <p class="text-lg text-muted-foreground mb-8">
        Join thousands of photographers in the fight against AI-generated imagery
      </p>
      <Button size="lg" @click="router.push('/register')">
        Create Your Account
      </Button>
    </div>
  </div>
</template>
