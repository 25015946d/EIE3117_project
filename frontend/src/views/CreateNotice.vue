<template>
  <div>
    <h1>Create Notice</h1>

    <div v-if="!isAuthenticated" class="card">
      <p>Please login first</p>
      <router-link to="/login" class="btn">Go to Login</router-link>
    </div>

    <div class="card" v-else>
      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <form @submit.prevent="submitNotice">
        <div class="form-group">
          <label class="form-label" for="title">Title</label>
          <input id="title" v-model="form.title" class="form-control" required />
        </div>

        <div class="form-group">
          <label class="form-label" for="type">Type</label>
          <select id="type" v-model="form.type" class="form-control" required>
            <option disabled value="">Select type</option>
            <option value="lost">Lost Item</option>
            <option value="found">Found Item</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label" for="date">Date</label>
          <input id="date" v-model="form.date" type="date" class="form-control" required />
        </div>

        <div class="form-group">
          <label class="form-label" for="venue">Venue</label>
          <input id="venue" v-model="form.venue" class="form-control" required />
        </div>

        <div class="form-group">
          <label class="form-label" for="contact">Contact</label>
          <input id="contact" v-model="form.contact" class="form-control" required />
        </div>

        <div class="form-group">
          <label class="form-label" for="description">Description</label>
          <textarea id="description" v-model="form.description" class="form-control" rows="4" required></textarea>
        </div>

        <div class="form-group">
          <label class="form-label" for="image">Image (optional)</label>
          <input id="image" type="file" class="form-control" accept="image/*" @change="onFileChange" />
        </div>

        <button class="btn" :disabled="loading">{{ loading ? 'Submitting...' : 'Create Notice' }}</button>
      </form>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import axios from 'axios'

export default {
  name: 'CreateNotice',
  data() {
    return {
      form: {
        title: '',
        type: '',
        date: '',
        venue: '',
        contact: '',
        description: '',
        image: null
      },
      loading: false,
      error: null
    }
  },
  computed: {
    ...mapGetters(['isAuthenticated'])
  },
  methods: {
    onFileChange(event) {
      const [file] = event.target.files
      this.form.image = file || null
    },
    async submitNotice() {
      this.loading = true
      this.error = null
      try {
        const data = new FormData()
        Object.entries(this.form).forEach(([key, value]) => {
          if (value !== null && value !== '') data.append(key, value)
        })
        const response = await axios.post('/notices/', data)
        this.$router.push(`/notice/${response.data.id}`)
      } catch (error) {
        const payload = error.response?.data || {}
        const firstKey = Object.keys(payload)[0]
        this.error = Array.isArray(payload[firstKey]) ? payload[firstKey][0] : 'Failed to create notice.'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
