<template>
  <div>
    <div v-if="loading" class="alert">Loading...</div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>

    <div v-else class="card notice-card" :class="notice.type">
      <div class="notice-header">
        <h1>{{ notice.title }}</h1>
        <span class="notice-type" :class="notice.type">{{ notice.type.toUpperCase() }}</span>
      </div>

      <p><strong>Date:</strong> {{ formatDate(notice.date) }}</p>
      <p><strong>Venue:</strong> {{ notice.venue }}</p>
      <p><strong>Contact:</strong> {{ notice.contact }}</p>
      <p><strong>Description:</strong> {{ notice.description }}</p>
      <p><strong>Owner:</strong> {{ notice.owner_nickname }} ({{ notice.owner_email }})</p>
      <p><strong>Status:</strong> {{ notice.status }}</p>

      <div v-if="isOwner" class="notice-actions">
        <button v-if="notice.status === 'active'" class="btn btn-success" @click="completeNotice" :disabled="completeLoading">
          {{ completeLoading ? 'Completing...' : 'Mark as Complete' }}
        </button>
        <button class="btn btn-danger" @click="deleteNotice" :disabled="deleteLoading">
          {{ deleteLoading ? 'Deleting...' : 'Delete Notice' }}
        </button>
        <div v-if="completeError" class="alert alert-error">{{ completeError }}</div>
        <div v-if="deleteError" class="alert alert-error">{{ deleteError }}</div>
      </div>

      <div v-if="notice.image" class="notice-image">
        <p>Debug: Image URL = {{ notice.image }}</p>
        <img :src="notice.image" :alt="notice.title" @error="onImageError" @load="onImageLoad" />
      </div>
      <div v-else class="alert">
        No image available for this notice.
      </div>

      <div v-if="canRespond" class="response-box">
        <h3>Respond to this notice</h3>
        <div v-if="respondError" class="alert alert-error">{{ respondError }}</div>
        <textarea v-model="responseMessage" class="form-control" rows="3" placeholder="Type your message"></textarea>
        <button class="btn" @click="submitResponse" :disabled="respondLoading || !responseMessage.trim()">
          {{ respondLoading ? 'Sending...' : 'Send Response' }}
        </button>
      </div>

      <div class="responses">
        <h3>Responses</h3>
        <div v-if="!notice.responses || notice.responses.length === 0" class="alert">No responses yet.</div>
        <div v-for="res in notice.responses" :key="res.id" class="card">
          <p><strong>{{ res.responder_nickname }}</strong> ({{ res.responder_email }})</p>
          <p>{{ res.message }}</p>
          <small>{{ formatDateTime(res.created_at) }}</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { mapGetters } from 'vuex'

export default {
  name: 'NoticeDetail',
  data() {
    return {
      notice: null,
      loading: false,
      error: null,
      responseMessage: '',
      respondLoading: false,
      respondError: null,
      deleteLoading: false,
      deleteError: null,
      completeLoading: false,
      completeError: null
    }
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'currentUser']),
    isOwner() {
      return this.isAuthenticated && this.notice && this.currentUser && this.notice.owner_id === this.currentUser.id
    },
    canRespond() {
      if (!this.isAuthenticated || !this.notice || !this.currentUser) return false
      if (this.notice.status !== 'active') return false
      // Allow all authenticated users to respond, including the notice owner
      return true
    },
    canCompleteNotice() {
      return this.isOwner && this.notice.status === 'active'
    }
  },
  methods: {
    onImageError() {
      console.error('Failed to load image:', this.notice.image)
    },
    onImageLoad() {
      console.log('Image loaded successfully:', this.notice.image)
    },
    async fetchDetail() {
      this.loading = true
      this.error = null
      try {
        const response = await axios.get(`/notices/${this.$route.params.id}/`)
        this.notice = response.data
      } catch (error) {
        this.error = 'Failed to load notice details.'
      } finally {
        this.loading = false
      }
    },
    async submitResponse() {
      this.respondLoading = true
      this.respondError = null
      try {
        await axios.post(`/notices/${this.$route.params.id}/respond/`, {
          message: this.responseMessage.trim()
        })
        this.responseMessage = ''
        await this.fetchDetail()
      } catch (error) {
        const payload = error.response?.data || {}
        this.respondError = payload.error || payload.message || 'Failed to send response.'
      } finally {
        this.respondLoading = false
      }
    },
    async completeNotice() {
      if (!confirm('Are you sure you want to mark this notice as complete? This means you have found your item.')) {
        return
      }
      
      this.completeLoading = true
      this.completeError = null
      try {
        await axios.post(`/notices/${this.$route.params.id}/complete/`)
        await this.fetchDetail() // Refresh the notice data
      } catch (error) {
        const payload = error.response?.data || {}
        this.completeError = payload.error || payload.message || 'Failed to complete notice.'
      } finally {
        this.completeLoading = false
      }
    },
    async deleteNotice() {
      if (!confirm('Are you sure you want to delete this notice? This action cannot be undone.')) {
        return
      }
      
      this.deleteLoading = true
      this.deleteError = null
      try {
        await axios.delete(`/notices/${this.$route.params.id}/delete/`)
        this.$router.push('/')
      } catch (error) {
        const payload = error.response?.data || {}
        this.deleteError = payload.error || payload.message || 'Failed to delete notice.'
      } finally {
        this.deleteLoading = false
      }
    },
    formatDate(value) {
      return new Date(value).toLocaleDateString()
    },
    formatDateTime(value) {
      return new Date(value).toLocaleString()
    }
  },
  created() {
    this.fetchDetail()
  }
}
</script>

<style scoped>
.notice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.notice-type {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  color: #fff;
  font-size: 0.8rem;
}
.notice-type.lost {
  background: #d64545;
}
.notice-type.found {
  background: #2a9d6f;
}
.notice-image img {
  margin: 1rem 0;
  max-width: 100%;
  border-radius: 8px;
}
.notice-actions {
  margin: 1rem 0;
}
.notice-actions button {
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
}
.btn-danger {
  background: #dc3545;
  color: white;
}
.btn-danger:hover {
  background: #c82333;
}
.btn-success {
  background: #28a745;
  color: white;
}
.btn-success:hover {
  background: #218838;
}
.response-box {
  margin-top: 1.5rem;
}
.responses {
  margin-top: 1.5rem;
}
</style>
