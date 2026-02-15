<template>
  <div id="app">
    <header class="topbar">
      <h2 class="brand">Lost &amp; Found</h2>
      <nav class="nav">
        <router-link to="/">Home</router-link>
        <router-link to="/create">Create</router-link>
        <router-link to="/my-notices">My Notices</router-link>
        <router-link to="/profile">Profile</router-link>
        <router-link v-if="!isAuthenticated" to="/login">Login</router-link>
        <button v-else class="linklike" @click="logoutAndGo">Logout</button>
      </nav>
    </header>

    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'

export default {
  name: 'App',
  computed: {
    ...mapGetters(['isAuthenticated'])
  },
  methods: {
    ...mapActions(['logout']),
    async logoutAndGo() {
      await this.logout()
      this.$router.push('/login')
    }
  }
}
</script>

<style>
:root {
  --bg: #f5f7fb;
  --card: #ffffff;
  --text: #2c3e50;
  --muted: #6b7280;
  --primary: #3498db;
  --danger: #d64545;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, 'Noto Sans', 'Helvetica Neue', sans-serif;
  background: var(--bg);
  color: var(--text);
}

#app {
  min-height: 100vh;
}

.topbar {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: var(--card);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  z-index: 10;
}

.brand {
  margin: 0;
  font-size: 1.1rem;
}

.nav {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.nav a {
  color: var(--text);
  text-decoration: none;
  padding: 0.25rem 0.4rem;
  border-radius: 6px;
}

.nav a.router-link-active {
  color: var(--primary);
  font-weight: 600;
}

.linklike {
  border: none;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  padding: 0.25rem 0.4rem;
  border-radius: 6px;
  font-size: inherit;
}

.linklike:hover,
.nav a:hover {
  background: rgba(0, 0, 0, 0.04);
}

.container {
  max-width: 960px;
  margin: 1.25rem auto;
  padding: 0 1rem;
}

.card {
  background: var(--card);
  border-radius: 10px;
  padding: 1rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
  margin-bottom: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.35rem;
}

.form-control {
  width: 100%;
  padding: 0.6rem 0.7rem;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: #fff;
  box-sizing: border-box;
  font-size: inherit;
}

.btn {
  display: inline-block;
  border: none;
  border-radius: 8px;
  padding: 0.6rem 0.9rem;
  background: var(--primary);
  color: #fff;
  cursor: pointer;
  font-weight: 600;
  text-decoration: none;
  font-size: inherit;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-danger {
  background: var(--danger);
}

.alert {
  padding: 0.75rem 0.9rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  background: rgba(0, 0, 0, 0.04);
}

.alert-error {
  background: rgba(214, 69, 69, 0.12);
  color: #7a1f1f;
}

.alert-success {
  background: rgba(42, 157, 111, 0.12);
  color: #11563d;
}
</style>
