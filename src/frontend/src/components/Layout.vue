<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Settings, Gavel, Plus, Menu, X, Trophy, Image, LogOut, Home } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Mobile menu state
const isMobileMenuOpen = ref(false)

const isAdmin = computed(() => authStore.user?.role === 'admin')
const isJudge = computed(() => authStore.user?.role === 'judge' || authStore.user?.role === 'admin')
const isOrganizer = computed(() => authStore.user?.role === 'organizer' || authStore.user?.role === 'admin')

const currentYear = new Date().getFullYear()

// Close mobile menu on route change
watch(() => route.path, () => {
  isMobileMenuOpen.value = false
})

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

const handleLogout = async () => {
  closeMobileMenu()
  await authStore.logout()
  router.push('/login')
}

const getInitials = (name?: string, username?: string) => {
  if (name) {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }
  return username?.slice(0, 2).toUpperCase() || 'U'
}

const getRoleBadgeVariant = (role?: string) => {
  switch (role) {
    case 'admin': return 'default'
    case 'judge': return 'info'
    case 'organizer': return 'secondary'
    default: return 'outline'
  }
}
</script>

<template>
  <div class="flex flex-col min-h-screen bg-background">
    <a
      href="#main"
      class="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[60] focus:rounded-full focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:text-primary-foreground"
    >
      Skip to content
    </a>

    <!-- Navigation -->
    <header class="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-md">
      <div class="container flex items-center justify-between h-16 px-4 md:px-6">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2" aria-label="A.V.A.R. home" @click="closeMobileMenu">
          <span class="h-2.5 w-2.5 rounded-full bg-brand" aria-hidden="true" />
          <span class="font-display text-xl font-bold tracking-tight text-foreground">
            A.V.A.R.
          </span>
        </router-link>

        <!-- Desktop Navigation -->
        <nav aria-label="Main" class="hidden md:flex items-center gap-1 text-sm">
          <router-link
            to="/competitions"
            class="rounded-full px-3.5 py-2 font-medium transition-colors hover:text-foreground hover:bg-accent"
            :class="route.path.startsWith('/competitions') ? 'text-foreground bg-accent' : 'text-muted-foreground'"
          >
            Competitions
          </router-link>
          <router-link
            v-if="authStore.isAuthenticated"
            to="/my-submissions"
            class="rounded-full px-3.5 py-2 font-medium transition-colors hover:text-foreground hover:bg-accent"
            :class="route.path.startsWith('/my-submissions') ? 'text-foreground bg-accent' : 'text-muted-foreground'"
          >
            My Submissions
          </router-link>

          <!-- Role-specific navigation -->
          <router-link
            v-if="isOrganizer"
            to="/organizer"
            class="flex items-center gap-1.5 rounded-full px-3.5 py-2 font-medium transition-colors hover:text-foreground hover:bg-accent"
            :class="route.path.startsWith('/organizer') ? 'text-foreground bg-accent' : 'text-muted-foreground'"
          >
            <Plus class="w-4 h-4" />
            Organizer Panel
          </router-link>
          <router-link
            v-if="isJudge"
            to="/judge"
            class="flex items-center gap-1.5 rounded-full px-3.5 py-2 font-medium transition-colors hover:text-foreground hover:bg-accent"
            :class="route.path.startsWith('/judge') ? 'text-foreground bg-accent' : 'text-muted-foreground'"
          >
            <Gavel class="w-4 h-4" />
            Judge Panel
          </router-link>
          <router-link
            v-if="isAdmin"
            to="/admin"
            class="flex items-center gap-1.5 rounded-full px-3.5 py-2 font-medium transition-colors hover:text-foreground hover:bg-accent"
            :class="route.path.startsWith('/admin') ? 'text-foreground bg-accent' : 'text-muted-foreground'"
          >
            <Settings class="w-4 h-4" />
            Admin Panel
          </router-link>
        </nav>

        <!-- Desktop Auth Buttons -->
        <div class="hidden md:flex items-center gap-3">
          <template v-if="authStore.isAuthenticated">
            <Badge :variant="getRoleBadgeVariant(authStore.user?.role)">
              {{ authStore.user?.role?.toUpperCase() }}
            </Badge>
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="ghost" size="icon" class="rounded-full" aria-label="Open account menu">
                  <Avatar class="w-10 h-10">
                    <AvatarFallback class="text-sm font-display font-semibold bg-ink text-ink-foreground">
                      {{ getInitials(authStore.user?.full_name, authStore.user?.username) }}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" class="w-56 rounded-2xl">
                <DropdownMenuLabel class="p-3">
                  <div class="flex flex-col space-y-1">
                    <p class="text-sm font-medium leading-none">{{ authStore.user?.username }}</p>
                    <p class="text-xs leading-none text-muted-foreground">{{ authStore.user?.email }}</p>
                    <Badge :variant="getRoleBadgeVariant(authStore.user?.role)" class="mt-2 w-fit">
                      {{ authStore.user?.role?.toUpperCase() }}
                    </Badge>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem as-child class="py-2 cursor-pointer rounded-lg">
                  <router-link to="/my-submissions">My Submissions</router-link>
                </DropdownMenuItem>
                <DropdownMenuItem v-if="isOrganizer" as-child class="py-2 cursor-pointer rounded-lg">
                  <router-link to="/organizer">
                    <Plus class="w-4 h-4 mr-2" />
                    Organizer Panel
                  </router-link>
                </DropdownMenuItem>
                <DropdownMenuItem v-if="isJudge" as-child class="py-2 cursor-pointer rounded-lg">
                  <router-link to="/judge">
                    <Gavel class="w-4 h-4 mr-2" />
                    Judge Panel
                  </router-link>
                </DropdownMenuItem>
                <DropdownMenuItem v-if="isAdmin" as-child class="py-2 cursor-pointer rounded-lg">
                  <router-link to="/admin">
                    <Settings class="w-4 h-4 mr-2" />
                    Admin Panel
                  </router-link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem @click="handleLogout" class="py-2 cursor-pointer rounded-lg text-destructive">
                  <LogOut class="w-4 h-4 mr-2" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </template>
          <template v-else>
            <Button variant="ghost" as-child>
              <router-link to="/login">Sign in</router-link>
            </Button>
            <Button as-child class="px-6">
              <router-link to="/register">Sign up</router-link>
            </Button>
          </template>
        </div>

        <!-- Mobile Menu Button -->
        <Button
          variant="ghost"
          size="icon"
          class="md:hidden"
          @click="toggleMobileMenu"
          :aria-expanded="isMobileMenuOpen"
          :aria-label="isMobileMenuOpen ? 'Close menu' : 'Open menu'"
        >
          <Menu v-if="!isMobileMenuOpen" class="w-6 h-6" />
          <X v-else class="w-6 h-6" />
        </Button>
      </div>

      <!-- Mobile Menu Panel -->
      <div
        v-if="isMobileMenuOpen"
        class="md:hidden border-t bg-background"
      >
        <nav aria-label="Mobile" class="container px-4 py-4 space-y-1">
          <!-- User info (if authenticated) -->
          <div v-if="authStore.isAuthenticated" class="flex items-center gap-3 px-3 py-3 mb-3 bg-secondary rounded-2xl">
            <Avatar class="w-10 h-10">
              <AvatarFallback class="text-sm font-display font-semibold bg-ink text-ink-foreground">
                {{ getInitials(authStore.user?.full_name, authStore.user?.username) }}
              </AvatarFallback>
            </Avatar>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate">{{ authStore.user?.username }}</p>
              <p class="text-xs text-muted-foreground truncate">{{ authStore.user?.email }}</p>
            </div>
            <Badge :variant="getRoleBadgeVariant(authStore.user?.role)" class="text-xs">
              {{ authStore.user?.role?.toUpperCase() }}
            </Badge>
          </div>

          <!-- Navigation Links -->
          <router-link
            to="/"
            class="flex items-center gap-3 px-3 py-3 rounded-xl text-base font-medium transition-colors hover:bg-accent"
            @click="closeMobileMenu"
          >
            <Home class="w-5 h-5 text-muted-foreground" />
            Home
          </router-link>

          <router-link
            to="/competitions"
            class="flex items-center gap-3 px-3 py-3 rounded-xl text-base font-medium transition-colors hover:bg-accent"
            @click="closeMobileMenu"
          >
            <Trophy class="w-5 h-5 text-muted-foreground" />
            Competitions
          </router-link>

          <router-link
            v-if="authStore.isAuthenticated"
            to="/my-submissions"
            class="flex items-center gap-3 px-3 py-3 rounded-xl text-base font-medium transition-colors hover:bg-accent"
            @click="closeMobileMenu"
          >
            <Image class="w-5 h-5 text-muted-foreground" />
            My Submissions
          </router-link>

          <!-- Role-specific links -->
          <div v-if="authStore.isAuthenticated && (isOrganizer || isJudge || isAdmin)" class="pt-2 mt-2 border-t">
            <p class="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Management
            </p>

            <router-link
              v-if="isOrganizer"
              to="/organizer"
              class="flex items-center gap-3 px-3 py-3 rounded-xl text-base font-medium transition-colors hover:bg-accent"
              @click="closeMobileMenu"
            >
              <Plus class="w-5 h-5 text-muted-foreground" />
              Organizer Panel
            </router-link>

            <router-link
              v-if="isJudge"
              to="/judge"
              class="flex items-center gap-3 px-3 py-3 rounded-xl text-base font-medium transition-colors hover:bg-accent"
              @click="closeMobileMenu"
            >
              <Gavel class="w-5 h-5 text-muted-foreground" />
              Judge Panel
            </router-link>

            <router-link
              v-if="isAdmin"
              to="/admin"
              class="flex items-center gap-3 px-3 py-3 rounded-xl text-base font-medium transition-colors hover:bg-accent"
              @click="closeMobileMenu"
            >
              <Settings class="w-5 h-5 text-muted-foreground" />
              Admin Panel
            </router-link>
          </div>

          <!-- Auth Actions -->
          <div class="pt-2 mt-2 border-t">
            <template v-if="authStore.isAuthenticated">
              <button
                type="button"
                @click="handleLogout"
                class="flex items-center gap-3 w-full px-3 py-3 rounded-xl text-base font-medium transition-colors hover:bg-accent text-destructive cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <LogOut class="w-5 h-5" />
                Log out
              </button>
            </template>
            <template v-else>
              <router-link
                to="/login"
                class="flex items-center justify-center w-full px-3 py-3 rounded-full text-base font-medium transition-colors hover:bg-accent border"
                @click="closeMobileMenu"
              >
                Sign in
              </router-link>
              <router-link
                to="/register"
                class="flex items-center justify-center w-full px-3 py-3 mt-2 rounded-full text-base font-medium bg-primary text-primary-foreground hover:bg-primary/85"
                @click="closeMobileMenu"
              >
                Sign up
              </router-link>
            </template>
          </div>
        </nav>
      </div>
    </header>

    <!-- Mobile Menu Overlay -->
    <div
      v-if="isMobileMenuOpen"
      class="fixed inset-0 top-16 z-40 bg-background/80 backdrop-blur-sm md:hidden"
      @click="closeMobileMenu"
    />

    <!-- Main Content -->
    <main id="main" class="flex-1">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="border-t overflow-hidden">
      <div class="container px-4 md:px-6 pt-10">
        <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-8">
          <div class="max-w-sm">
            <div class="flex items-center gap-2">
              <span class="h-2.5 w-2.5 rounded-full bg-brand" aria-hidden="true" />
              <span class="font-display text-lg font-bold tracking-tight">A.V.A.R.</span>
            </div>
            <p class="mt-2 text-sm text-muted-foreground">
              Authenticity Verification And Rating — AI-verified photography competitions with human judging.
            </p>
          </div>
          <nav aria-label="Footer" class="flex gap-12 text-sm">
            <div class="space-y-2">
              <p class="font-medium">Platform</p>
              <div class="flex flex-col gap-2 text-muted-foreground">
                <router-link to="/competitions" class="hover:text-foreground transition-colors">Competitions</router-link>
                <router-link to="/my-submissions" class="hover:text-foreground transition-colors">My Submissions</router-link>
                <router-link to="/register" class="hover:text-foreground transition-colors">Create account</router-link>
              </div>
            </div>
          </nav>
        </div>
        <p class="mt-10 pb-4 text-xs text-muted-foreground">
          © {{ currentYear }} A.V.A.R. — Authenticity Verification And Rating
        </p>
      </div>
      <div aria-hidden="true" class="pointer-events-none select-none -mb-[4vw]">
        <p class="text-center font-display font-bold tracking-tighter leading-none text-[19vw] text-foreground/[0.05]">
          A.V.A.R.
        </p>
      </div>
    </footer>
  </div>
</template>
