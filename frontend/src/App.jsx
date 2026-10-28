import { Navigate, Route, Routes } from 'react-router-dom'
import { LandingPage } from '@/features/landing/LandingPage'
import { LoginPage } from '@/features/auth/LoginPage'
import { SignupPage } from '@/features/auth/SignupPage'
import { ForgotPasswordPage } from '@/features/auth/ForgotPasswordPage'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { AppShell } from '@/features/workspaces/AppShell'
import { WorkspaceCreatePage } from '@/features/workspaces/WorkspaceCreatePage'
import { MembersPage } from '@/features/workspaces/MembersPage'
import { SettingsPage } from '@/features/workspaces/SettingsPage'
import { OverviewPage } from '@/features/dashboard/OverviewPage'
import { ProjectsPage } from '@/features/projects/ProjectsPage'
import { ProjectCreatePage } from '@/features/projects/ProjectCreatePage'
import { ProjectShell } from '@/features/projects/ProjectShell'
import { ProjectSettingsPage } from '@/features/projects/ProjectSettingsPage'
import { BacklogPage } from '@/features/projects/BacklogPage'
import { ReportsPage } from '@/features/projects/ReportsPage'
import { IssuesNavigatorPage } from '@/features/projects/IssuesNavigatorPage'
import { ReleasesPage } from '@/features/projects/ReleasesPage'
import { ComponentsPage } from '@/features/projects/ComponentsPage'
import { ProjectSummaryPage } from '@/features/projects/ProjectSummaryPage'
import { KanbanBoardPage } from '@/features/tasks/KanbanBoardPage'
import { TaskDetailPage } from '@/features/tasks/TaskDetailPage'
import { MyTasksPage } from '@/features/tasks/MyTasksPage'
import { ActivityPage } from '@/features/activity/ActivityPage'
import { AppHomeRedirect } from '@/features/workspaces/AppHomeRedirect'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/app" element={<AppHomeRedirect />} />
      <Route path="/app/workspaces/new" element={<WorkspaceCreatePage />} />
      <Route
        path="/app/:workspaceSlug"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<OverviewPage />} />
        <Route path="my-tasks" element={<MyTasksPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/new" element={<ProjectCreatePage />} />
        <Route path="projects/:projectKey" element={<ProjectShell />}>
          <Route index element={<Navigate to="board" replace />} />
          <Route path="summary" element={<ProjectSummaryPage />} />
          <Route path="backlog" element={<BacklogPage />} />
          <Route path="board" element={<KanbanBoardPage />} />
          <Route path="list" element={<IssuesNavigatorPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="issues" element={<IssuesNavigatorPage />} />
          <Route path="releases" element={<ReleasesPage />} />
          <Route path="components" element={<ComponentsPage />} />
          <Route path="settings" element={<ProjectSettingsPage />} />
        </Route>
        <Route path="activity" element={<ActivityPage />} />
        <Route path="members" element={<MembersPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="tasks/:taskId" element={<TaskDetailPage />} />
        <Route path="issues/:issueId" element={<TaskDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
