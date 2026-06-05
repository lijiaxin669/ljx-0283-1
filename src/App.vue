<template>
  <div class="min-h-screen bg-gradient-to-br from-sky-50 to-cyan-50">
    <header class="bg-white/80 backdrop-blur-sm border-b border-sky-100 sticky top-0 z-10">
      <div class="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2">
          <div class="w-10 h-10 bg-sky-500 rounded-xl flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
          </div>
          <span class="text-xl font-bold text-sky-900">少年宫亲子游泳班</span>
        </router-link>
        <nav class="flex gap-4 text-sm">
          <router-link to="/" class="px-3 py-2 rounded-lg hover:bg-sky-50 text-sky-800 transition">选班报名</router-link>
          <router-link to="/admin" class="px-3 py-2 rounded-lg hover:bg-sky-50 text-sky-800 transition">管理端</router-link>
        </nav>
      </div>
    </header>
    <main class="max-w-5xl mx-auto px-4 py-8">
      <router-view />
    </main>
  </div>
</template>
