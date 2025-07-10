
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useUserStatus } from '../hooks/useUserStatus';

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading: authLoading, user } = useAuth();
  const { isApproved, loading: statusLoading } = useUserStatus();

  if (authLoading || statusLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Verificar se é o admin principal (bypass da aprovação)
  if (user?.email === 'brendacostatrader@gmail.com') {
    return <>{children || <Outlet />}</>;
  }

  // Para outros usuários, verificar aprovação
  if (!isApproved) {
    return <Navigate to="/pending-approval" replace />;
  }

  return <>{children || <Outlet />}</>;
};

export default ProtectedRoute;
