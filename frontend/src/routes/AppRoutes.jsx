import { Navigate, Route, Routes } from "react-router-dom";

import DashboardLayout from "../components/layout/DashboardLayout";
import AdminDashboard from "../pages/admin/AdminDashboard";
import BusinessAnalytics from "../pages/admin/BusinessAnalytics";
import EmployeePerformance from "../pages/admin/EmployeePerformance";
import OfficePerformance from "../pages/admin/OfficePerformance";
import Login from "../pages/auth/Login";
import Landing from "../pages/Landing";
import Signup from "../pages/auth/Signup";
import CounsellorDashboard from "../pages/counsellor/CounsellorDashboard";
import CounsellorLeadDetails from "../pages/counsellor/LeadDetails";
import MyLeads from "../pages/counsellor/MyLeads";
import ManagerLeadDetails from "../pages/manager/LeadDetails";
import Leads from "../pages/manager/Leads";
import ManagerDashboard from "../pages/manager/ManagerDashboard";
import SourcePerformance from "../pages/manager/SourcePerformance";
import { ROLES } from "../utils/constants";
import ProtectedRoute from "./ProtectedRoute";

function protectedLayout(role) {
  return (
    <ProtectedRoute allowedRoles={[role]}>
      <DashboardLayout />
    </ProtectedRoute>
  );
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route path="/admin" element={protectedLayout(ROLES.ADMIN)}>
        <Route index element={<AdminDashboard />} />
        <Route path="offices" element={<OfficePerformance />} />
        <Route path="business" element={<BusinessAnalytics />} />
        <Route path="employees" element={<EmployeePerformance />} />
      </Route>

      <Route path="/manager" element={protectedLayout(ROLES.MANAGER)}>
        <Route index element={<ManagerDashboard />} />
        <Route path="leads" element={<Leads />} />
        <Route path="leads/:id" element={<ManagerLeadDetails />} />
        <Route path="sources" element={<SourcePerformance />} />
      </Route>

      <Route path="/counsellor" element={protectedLayout(ROLES.COUNSELLOR)}>
        <Route index element={<CounsellorDashboard />} />
        <Route path="leads" element={<MyLeads />} />
        <Route path="leads/:id" element={<CounsellorLeadDetails />} />
      </Route>

      <Route path="/unauthorized" element={<div className="screen-center"><h2>Access denied</h2></div>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
