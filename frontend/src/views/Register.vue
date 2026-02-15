<template>
  <div class="register">
    <div class="form-container">
      <h2>Create Account</h2>

      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label class="form-label" for="username">Login ID</label>
          <input id="username" v-model="form.username" type="text" class="form-control" required />
        </div>

        <div class="form-group">
          <label class="form-label" for="nickname">Nick Name</label>
          <input id="nickname" v-model="form.nickname" type="text" class="form-control" required />
        </div>

        <div class="form-group">
          <label class="form-label" for="email">Email</label>
          <input id="email" v-model="form.email" type="email" class="form-control" required />
        </div>

        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input id="password" v-model="form.password" type="password" class="form-control" required minlength="8" />
        </div>

        <div class="form-group">
          <label class="form-label" for="passwordConfirm">Confirm Password</label>
          <input id="passwordConfirm" v-model="form.password_confirm" type="password" class="form-control" required minlength="8" />
        </div>

        <div class="form-group">
          <label class="form-label" for="profileImage">Profile Image (optional)</label>
          <input id="profileImage" type="file" class="form-control" accept="image/*" @change="onFileChange" />
        </div>

        <button type="submit" class="btn" :disabled="loading">
          {{ loading ? 'Registering...' : 'Register' }}
        </button>
      </form>

      <p class="login-link">
        Already have an account?
        <router-link to="/login">Login here</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  name: 'Register',
  data() {
    return {
      form: {
        username: '',
        nickname: '',
        email: '',
        password: '',
        password_confirm: '',
        profile_image: null
      },
      loading: false,
      error: null
    }
  },
  methods: {
    ...mapActions(['register']),
    onFileChange(event) {
      const [file] = event.target.files
      this.form.profile_image = file || null
    },
    async handleRegister() {
      this.loading = true
      this.error = null
      try {
        const data = new FormData()
        Object.entries(this.form).forEach(([key, value]) => {
          if (value !== null && value !== '') data.append(key, value)
        })
        await this.register(data)
        this.$router.push('/')
      } catch (error) {
        const firstKey = Object.keys(error)[0]
        this.error = Array.isArray(error[firstKey]) ? error[firstKey][0] : 'Registration failed.'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.register {
  display: flex;
  justify-content: center;
  padding: 1rem 0 2rem;
}
.form-container {
  width: 100%;
  max-width: 520px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  padding: 1.5rem;
}
h2 {
  margin-bottom: 1rem;
}
.login-link {
  margin-top: 1rem;
}
</style>
