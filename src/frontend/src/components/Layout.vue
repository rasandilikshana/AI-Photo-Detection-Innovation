<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}

const getInitials = (name?: string, username?: string) => {
  if (name) {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }
  return username?.slice(0, 2).toUpperCase() || 'U'
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- Navigation -->
    <header class="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="container flex h-16 items-center">
        <div class="mr-4 flex">
          <router-link to="/" class="mr-6 flex items-center space-x-2">
            <span class="font-bold text-xl">A.V.A.R.</span>
          </router-link>
          <nav class="flex items-center space-x-6 text-sm font-medium">
            <router-link to="/competitions" class="transition-colors hover:text-foreground/80 text-foreground/60">
              Competitions
            </router-link>
            <router-link
              v-if="authStore.isAuthenticated"
              to="/my-submissions"
              class="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              My Submissions
            </router-link>
          </nav>
        </div>

        <div class="ml-auto flex items-center space-x-4">
          <template v-if="authStore.isAuthenticated">
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="ghost" class="relative h-10 w-10 rounded-full">
                  <Avatar>
                    <AvatarFallback>
                      {{ getInitials(authStore.user?.full_name, authStore.user?.username) }}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>
                  <div class="flex flex-col space-y-1">
                    <p class="text-sm font-medium leading-none">{{ authStore.user?.username }}</p>
                    <p class="text-xs leading-none text-muted-foreground">{{ authStore.user?.email }}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem as-child>
                  <router-link to="/my-submissions">My Submissions</router-link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem @click="handleLogout">
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </template>
          <template v-else>
            <Button variant="ghost" as-child>
              <router-link to="/login">Sign In</router-link>
            </Button>
            <Button as-child>
              <router-link to="/register">Sign Up</router-link>
            </Button>
          </template>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="border-t py-6 md:py-0">
      <div class="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
        <p class="text-center text-sm leading-loose text-muted-foreground md:text-left">
          © 2024 A.V.A.R. Anti-AI Verification and Adjudication Registry
        </p>
      </div>
    </footer>
  </div>
</template>
