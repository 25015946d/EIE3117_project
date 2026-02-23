<template>
  <div>
    <h1>All Notices</h1>
    <div v-if="loading" class="alert">Loading...</div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>

    <div v-else>
      <div v-if="notices.length === 0" class="alert">No notices found.</div>

      <div v-for="notice in notices" :key="notice.id" class="card notice-card" :class="notice.type">
        <div class="row">
          <div>
            <h3>{{ notice.title }}</h3>
            <p><strong>Type:</strong> {{ notice.type }}</p>
            <p><strong>Status:</strong> {{ notice.status }}</p>
            <p><strong>Posted by:</strong> {{ notice.owner_nickname || notice.owner_email }}</p>
            <p><strong>Date:</strong> {{ notice.date }}</p>
            <p><strong>Venue:</strong> {{ notice.venue }}</p>
            <p><strong>Responses:</strong> {{ notice.responses_count || 0 }}</p>
          </div>
          <div class="actions">
            <router-link class="btn" :to="`/notice/${notice.id}`">View Details</router-link>
            <button
              v-if="currentUser && notice.owner === currentUser.id && notice.status === 'active'"
              class="btn btn-danger"
              @click="markComplete(notice.id)"
            >
              Mark Complete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { mapGetters } from 'vuex'

export default {
  name: 'AllNotices',
  data() {
    return {
      notices: [],
      loading: false,
      error: null
    }
  },
  computed: {
    ...mapGetters(['currentUser'])
  },
  methods: {
    async fetchNotices() {
      this.loading = true
      this.error = null
      try {
        const response = await axios.get('/notices/')
        this.notices = response.data.results || response.data
      } catch (error) {
        this.error = 'Failed to load notices.'
      } finally {
        this.loading = false
      }
    },
    async markComplete(noticeId) {
      try {
        await axios.post(`/notices/${noticeId}/complete/`)
        await this.fetchNotices()
      } catch (error) {
        this.error = error.response?.data?.error || 'Failed to mark complete.'
      }
    }
  },
  created() {
    this.fetchNotices()
  }
}
</script>

<style scoped>
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}
.actions {
  display: flex;
  gap: 0.5rem;
  flex-direction: column;
}
.notice-card.lost {
  border-left: 4px solid var(--danger);
}
.notice-card.found {
  border-left: 4px solid var(--primary);
}
</style>
