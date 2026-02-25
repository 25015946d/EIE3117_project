<template>
  <div>
    <h1>My Profile</h1>

    <div v-if="!isAuthenticated" class="card">
      <p>Please login first</p>
      <router-link to="/login" class="btn">Go to Login</router-link>
    </div>

    <div class="card" v-else-if="currentUser">
      <div v-if="success" class="alert alert-success">{{ success }}</div>
      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <div class="profile-header">
        <img v-if="currentUser.profile_image" :src="currentUser.profile_image" alt="profile" class="profile-image" />
        <div>
          <p><strong>Email:</strong> {{ currentUser.email }}</p>
          <p><strong>Login ID:</strong> {{ currentUser.username }}</p>
        </div>
      </div>

      <form @submit.prevent="saveProfile">
        <div class="form-group">
          <label class="form-label" for="nickname">Nick Name</label>
          <input id="nickname" v-model="form.nickname" class="form-control" required />
        </div>

        <div class="form-group">
          <label class="form-label" for="profileImage">Profile Image</label>
          <input id="profileImage" type="file" class="form-control" accept="image/*" @change="onFileChange" />
        </div>

        <button class="btn" :disabled="loading">{{ loading ? 'Saving...' : 'Save Profile' }}</button>
      </form>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'Profile',
  data() {
    return {
      form: { nickname: '', profile_image: null },
      loading: false,
      error: null,
      success: null
    }
  },
  computed: {
    ...mapGetters(['currentUser', 'isAuthenticated'])
  },
  created() {
    if (this.currentUser) this.form.nickname = this.currentUser.nickname || ''
  },
  methods: {
    ...mapActions(['updateProfile']),
    onFileChange(event) {
      const [file] = event.target.files
      this.form.profile_image = file || null
    },
    async saveProfile() {
      this.loading = true
      this.error = null
      this.success = null
      try {
        const data = new FormData()
        data.append('nickname', this.form.nickname)
        if (this.form.profile_image) data.append('profile_image', this.form.profile_image)
        await this.updateProfile(data)
        this.success = 'Profile updated.'
      } catch (error) {
        const firstKey = Object.keys(error)[0]
        this.error = Array.isArray(error[firstKey]) ? error[firstKey][0] : 'Failed to update profile.'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.profile-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}
.profile-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 50%;
}
</style>
