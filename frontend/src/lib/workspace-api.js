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
  // Template seeding hits Neon several times; allow a long window.
  return api
    .post(`/workspaces/${slug}/projects/`, payload, { timeout: 90000 })
    .then((r) => r.data)
}

export function fetchProject(slug, projectKey) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/`)
    .then((r) => r.data)
}

export function updateProject(slug, projectKey, payload) {
  return api
    .patch(`/workspaces/${slug}/projects/${projectKey}/`, payload)
    .then((r) => r.data)
}

export function fetchProjectTemplates() {
  return api.get('/project-templates/').then((r) => r.data)
}

export function checkProjectKey(slug, key) {
  return api
    .get(`/workspaces/${slug}/projects/key-check/`, { params: { key } })
    .then((r) => r.data)
}

export function fetchWorkflow(slug, projectKey) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/workflow/`)
    .then((r) => r.data)
}

export function fetchBoard(slug, projectKey, params = {}) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/board/`, { params })
    .then((r) => r.data)
}

export function fetchBacklog(slug, projectKey) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/backlog/`)
    .then((r) => r.data)
}

export function fetchSprints(slug, projectKey) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/sprints/`)
    .then((r) => r.data)
}

export function createSprint(slug, projectKey, payload) {
  return api
    .post(`/workspaces/${slug}/projects/${projectKey}/sprints/`, payload)
    .then((r) => r.data)
}

export function startSprint(slug, projectKey, sprintId, payload = {}) {
  return api
    .post(
      `/workspaces/${slug}/projects/${projectKey}/sprints/${sprintId}/start/`,
      payload,
    )
    .then((r) => r.data)
}

export function completeSprint(slug, projectKey, sprintId, payload = {}) {
  return api
    .post(
      `/workspaces/${slug}/projects/${projectKey}/sprints/${sprintId}/complete/`,
      payload,
    )
    .then((r) => r.data)
}

export function fetchIssue(issueId) {
  return api.get(`/issues/${issueId}/`).then((r) => r.data)
}

export function fetchTask(taskId) {
  return fetchIssue(taskId)
}

export function updateIssue(issueId, payload) {
  return api.patch(`/issues/${issueId}/`, payload).then((r) => r.data)
}

export function updateTask(taskId, payload) {
  return updateIssue(taskId, payload)
}

export function updateIssuePosition(issueId, payload) {
  return api.patch(`/issues/${issueId}/position/`, payload).then((r) => r.data)
}

export function updateTaskPosition(taskId, payload) {
  return updateIssuePosition(taskId, payload)
}

export function fetchIssueTransitions(issueId) {
  return api.get(`/issues/${issueId}/transitions/`).then((r) => r.data)
}

export function applyIssueTransition(issueId, payload) {
  return api.post(`/issues/${issueId}/transitions/`, payload).then((r) => r.data)
}

export function fetchIssueHistory(issueId) {
  return api.get(`/issues/${issueId}/history/`).then((r) => r.data)
}

export function fetchIssueLinks(issueId) {
  return api.get(`/issues/${issueId}/links/`).then((r) => r.data)
}

export function createIssueLink(issueId, payload) {
  return api.post(`/issues/${issueId}/links/`, payload).then((r) => r.data)
}

export function rankIssue(issueId, payload) {
  return api.patch(`/issues/${issueId}/rank/`, payload).then((r) => r.data)
}

export function createIssue(slug, projectKey, payload) {
  return api
    .post(`/workspaces/${slug}/projects/${projectKey}/issues/`, payload)
    .then((r) => r.data)
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

export function fetchOnboarding(slug) {
  return api.get(`/workspaces/${slug}/onboarding/`).then((r) => r.data)
}

export function updateOnboarding(slug, payload) {
  return api.patch(`/workspaces/${slug}/onboarding/`, payload).then((r) => r.data)
}

export function fetchBurndown(slug, projectKey, sprintId) {
  return api
    .get(
      `/workspaces/${slug}/projects/${projectKey}/sprints/${sprintId}/burndown/`,
    )
    .then((r) => r.data)
}

export function fetchVelocity(slug, projectKey) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/reports/velocity/`)
    .then((r) => r.data)
}

export function fetchCfd(slug, projectKey, params = {}) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/reports/cfd/`, { params })
    .then((r) => r.data)
}

export function fetchCreatedVsResolved(slug, projectKey) {
  return api
    .get(
      `/workspaces/${slug}/projects/${projectKey}/reports/created-vs-resolved/`,
    )
    .then((r) => r.data)
}

export function fetchBreakdown(slug, projectKey, by = 'priority') {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/reports/breakdown/`, {
      params: { by },
    })
    .then((r) => r.data)
}

export function fetchProjectSummary(slug, projectKey) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/reports/summary/`)
    .then((r) => r.data)
}

export function fetchIssueNavigator(slug, params = {}) {
  return api
    .get(`/workspaces/${slug}/issue-navigator/`, { params })
    .then((r) => r.data)
}

export function fetchWorkspaceSearch(slug, q) {
  return api
    .get(`/workspaces/${slug}/search/`, { params: { q } })
    .then((r) => r.data)
}

export function fetchReleases(slug, projectKey) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/releases/`)
    .then((r) => r.data)
}

export function createRelease(slug, projectKey, payload) {
  return api
    .post(`/workspaces/${slug}/projects/${projectKey}/releases/`, payload)
    .then((r) => r.data)
}

export function fetchReleaseDetail(slug, projectKey, releaseId) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/releases/${releaseId}/`)
    .then((r) => r.data)
}

export function publishRelease(slug, projectKey, releaseId, payload = {}) {
  return api
    .post(
      `/workspaces/${slug}/projects/${projectKey}/releases/${releaseId}/publish/`,
      payload,
    )
    .then((r) => r.data)
}

export function fetchReleaseNotes(slug, projectKey, releaseId) {
  return api
    .get(
      `/workspaces/${slug}/projects/${projectKey}/releases/${releaseId}/notes/`,
    )
    .then((r) => r.data)
}

export function fetchComponents(slug, projectKey) {
  return api
    .get(`/workspaces/${slug}/projects/${projectKey}/components/`)
    .then((r) => r.data)
}

export function createComponent(slug, projectKey, payload) {
  return api
    .post(`/workspaces/${slug}/projects/${projectKey}/components/`, payload)
    .then((r) => r.data)
}

export function fetchNotifications(slug) {
  return api.get(`/workspaces/${slug}/notifications/`).then((r) => r.data)
}

export function markNotificationRead(slug, notificationId) {
  return api
    .post(`/workspaces/${slug}/notifications/${notificationId}/read/`)
    .then((r) => r.data)
}

export function unwrapList(data) {
  if (Array.isArray(data)) return data
  if (data?.results) return data.results
  return []
}
