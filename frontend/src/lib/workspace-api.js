import { api } from '@/lib/api'

export function fetchWorkspaces() {
  return api.get('/workspaces/').then((r) => r.data)
}

export function fetchWorkspace(slug) {
  return api.get(`/workspaces/${slug}/`).then((r) => r.data)
}

export function createWorkspace(payload) {
  return api.post('/workspaces/', payload).then((r) => r.data)
}

export function fetchDashboard(slug) {
  return api.get(`/workspaces/${slug}/dashboard/`).then((r) => r.data)
}

export function fetchProjects(slug, params = {}) {
  return api.get(`/workspaces/${slug}/projects/`, { params }).then((r) => r.data)
}

export function createProject(slug, payload) {
  return api.post(`/workspaces/${slug}/projects/`, payload).then((r) => r.data)
}

export function fetchBoard(slug, projectKey) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/board/`)
    .then((r) => r.data)
}

export function fetchTask(taskId) {
  return api.get(`/tasks/${taskId}/`).then((r) => r.data)
}

export function updateTask(taskId, payload) {
  return api.patch(`/tasks/${taskId}/`, payload).then((r) => r.data)
}

export function updateTaskPosition(taskId, payload) {
  return api.patch(`/tasks/${taskId}/position/`, payload).then((r) => r.data)
}

export function fetchComments(taskId) {
  return api.get(`/tasks/${taskId}/comments/`).then((r) => r.data)
}

export function postComment(taskId, body) {
  return api.post(`/tasks/${taskId}/comments/`, { body }).then((r) => r.data)
}

export function fetchMembers(slug, params = {}) {
  return api.get(`/workspaces/${slug}/members/`, { params }).then((r) => r.data)
}

export function fetchMemberStats(slug) {
  return api.get(`/workspaces/${slug}/members/stats/`).then((r) => r.data)
}

export function inviteMember(slug, payload) {
  return api.post(`/workspaces/${slug}/members/`, payload).then((r) => r.data)
}

export function updateMemberRole(slug, membershipId, role) {
  return api
    .patch(`/workspaces/${slug}/members/${membershipId}/`, { role })
    .then((r) => r.data)
}

export function fetchActivity(slug, params = {}) {
  return api.get(`/workspaces/${slug}/activity/`, { params }).then((r) => r.data)
}

export function fetchActivityStats(slug) {
  return api.get(`/workspaces/${slug}/activity/stats/`).then((r) => r.data)
}

export function unwrapList(data) {
  if (Array.isArray(data)) return data
  if (data?.results) return data.results
  return []
}
