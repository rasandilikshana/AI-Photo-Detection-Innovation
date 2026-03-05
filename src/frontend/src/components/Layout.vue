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
    case 'admin': return 'destructive'
    case 'judge': return 'secondary'
    case 'organizer': return 'default'
    default: return 'outline'
  }
}
</script>

<template>
  <div class="flex flex-col min-h-screen bg-background">
    <!-- Navigation -->
    <header class="sticky top-0 z-50 w-full border-b bg-card/95 backdrop-blur-sm">
      <div class="container flex items-center justify-between h-16 px-4 md:px-6">
        <!-- Logo -->
        <router-link to="/" class="flex items-center" @click="closeMobileMenu">
          <span class="text-xl font-bold text-primary">
            A.V.A.R.
          </span>
        </router-link>

        <!-- Desktop Navigation -->
        <nav class="hidden md:flex items-center space-x-6 text-base">
          <router-link
            to="/competitions"
            class="font-medium transition-colors hover:text-foreground text-muted-foreground"
          >
            Competitions
          </router-link>
          <router-link
            v-if="authStore.isAuthenticated"
            to="/my-submissions"
            class="font-medium transition-colors hover:text-foreground text-muted-foreground"
          >
            My Submissions
          </router-link>

          <!-- Role-specific navigation -->
          <router-link
            v-if="isOrganizer"
            to="/organizer"
            class="flex items-center gap-1.5 transition-colors hover:text-foreground text-muted-foreground font-medium"
          >
            <Plus class="w-4 h-4" />
            Create Competition
          </router-link>
          <router-link
            v-if="isJudge"
            to="/judge"
            class="flex items-center gap-1.5 transition-colors hover:text-foreground text-muted-foreground font-medium"
          >
            <Gavel class="w-4 h-4" />
            Judge Panel
          </router-link>
          <router-link
            v-if="isAdmin"
            to="/admin"
            class="flex items-center gap-1.5 transition-colors hover:text-foreground text-muted-foreground font-medium"
          >
            <Settings class="w-4 h-4" />
            Admin
          </router-link>
        </nav>

        <!-- Desktop Auth Buttons -->
        <div class="hidden md:flex items-center space-x-4">
          <template v-if="authStore.isAuthenticated">
            <Badge :variant="getRoleBadgeVariant(authStore.user?.role)" class="hidden sm:flex">
              {{ authStore.user?.role?.toUpperCase() }}
            </Badge>
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="ghost" class="relative w-10 h-10 rounded-full">
                  <Avatar class="w-10 h-10">
                    <AvatarFallback class="text-base font-medium bg-primary/10 text-primary">
                      {{ getInitials(authStore.user?.full_name, authStore.user?.username) }}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" class="w-56">
                <DropdownMenuLabel class="p-3">
                  <div class="flex flex-col space-y-1">
                    <p class="text-base font-medium leading-none">{{ authStore.user?.username }}</p>
                    <p class="text-sm leading-none text-muted-foreground">{{ authStore.user?.email }}</p>
                    <Badge :variant="getRoleBadgeVariant(authStore.user?.role)" class="mt-2 w-fit">
                      {{ authStore.user?.role?.toUpperCase() }}
                    </Badge>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem as-child class="py-2 text-base cursor-pointer">
                  <router-link to="/my-submissions">My Submissions</router-link>
                </DropdownMenuItem>
                <DropdownMenuItem v-if="isOrganizer" as-child class="py-2 text-base cursor-pointer">
                  <router-link to="/organizer">
                    <Plus class="w-4 h-4 mr-2" />
                    Create Competition
                  </router-link>
                </DropdownMenuItem>
                <DropdownMenuItem v-if="isJudge" as-child class="py-2 text-base cursor-pointer">
                  <router-link to="/judge">
                    <Gavel class="w-4 h-4 mr-2" />
                    Judge Dashboard
                  </router-link>
                </DropdownMenuItem>
                <DropdownMenuItem v-if="isAdmin" as-child class="py-2 text-base cursor-pointer">
                  <router-link to="/admin">
                    <Settings class="w-4 h-4 mr-2" />
                    Admin Panel
                  </router-link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem @click="handleLogout" class="py-2 text-base cursor-pointer">
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </template>
          <template v-else>
            <Button variant="ghost" as-child class="text-base">
              <router-link to="/login">Sign In</router-link>
            </Button>
            <Button as-child class="px-6 text-base">
              <router-link to="/register">Sign Up</router-link>
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
          aria-label="Toggle menu"
        >
          <Menu v-if="!isMobileMenuOpen" class="w-6 h-6" />
          <X v-else class="w-6 h-6" />
        </Button>
      </div>

      <!-- Mobile Menu Panel -->
      <div
        v-if="isMobileMenuOpen"
        class="md:hidden border-t bg-card"
      >
        <nav class="container px-4 py-4 space-y-1">
          <!-- User info (if authenticated) -->
          <div v-if="authStore.isAuthenticated" class="flex items-center gap-3 px-3 py-3 mb-3 bg-muted/50 rounded-lg">
            <Avatar class="w-10 h-10">
              <AvatarFallback class="text-base font-medium bg-primary/10 text-primary">
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
            class="flex items-center gap-3 px-3 py-3 rounded-lg text-base font-medium transition-colors hover:bg-muted"
            @click="closeMobileMenu"
          >
            <Home class="w-5 h-5 text-muted-foreground" />
            Home
          </router-link>

          <router-link
            to="/competitions"
            class="flex items-center gap-3 px-3 py-3 rounded-lg text-base font-medium transition-colors hover:bg-muted"
            @click="closeMobileMenu"
          >
            <Trophy class="w-5 h-5 text-muted-foreground" />
            Competitions
          </router-link>

          <router-link
            v-if="authStore.isAuthenticated"
            to="/my-submissions"
            class="flex items-center gap-3 px-3 py-3 rounded-lg text-base font-medium transition-colors hover:bg-muted"
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
              class="flex items-center gap-3 px-3 py-3 rounded-lg text-base font-medium transition-colors hover:bg-muted"
              @click="closeMobileMenu"
            >
              <Plus class="w-5 h-5 text-muted-foreground" />
              Create Competition
            </router-link>

            <router-link
              v-if="isJudge"
              to="/judge"
              class="flex items-center gap-3 px-3 py-3 rounded-lg text-base font-medium transition-colors hover:bg-muted"
              @click="closeMobileMenu"
            >
              <Gavel class="w-5 h-5 text-muted-foreground" />
              Judge Panel
            </router-link>

            <router-link
              v-if="isAdmin"
              to="/admin"
              class="flex items-center gap-3 px-3 py-3 rounded-lg text-base font-medium transition-colors hover:bg-muted"
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
                @click="handleLogout"
                class="flex items-center gap-3 w-full px-3 py-3 rounded-lg text-base font-medium transition-colors hover:bg-muted text-destructive"
              >
                <LogOut class="w-5 h-5" />
                Log out
              </button>
            </template>
            <template v-else>
              <router-link
                to="/login"
                class="flex items-center justify-center w-full px-3 py-3 rounded-lg text-base font-medium transition-colors hover:bg-muted"
                @click="closeMobileMenu"
              >
                Sign In
              </router-link>
              <router-link
                to="/register"
                class="flex items-center justify-center w-full px-3 py-3 mt-2 rounded-lg text-base font-medium bg-primary text-primary-foreground hover:bg-primary/90"
                @click="closeMobileMenu"
              >
                Sign Up
              </router-link>
            </template>
          </div>
        </nav>
      </div>
    </header>

    <!-- Mobile Menu Overlay -->
    <div
      v-if="isMobileMenuOpen"
      class="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
      style="top: 64px;"
      @click="closeMobileMenu"
    />

    <!-- Main Content -->
    <main class="flex-1">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="py-6 border-t">
      <div class="container px-4 md:px-6">
        <p class="text-sm md:text-base text-center text-muted-foreground">
          © 2026 <span class="font-semibold text-primary">A.V.A.R.</span> - Authenticity Verification And Rating
        </p>
      </div>
    </footer>
  </div>
</template>
