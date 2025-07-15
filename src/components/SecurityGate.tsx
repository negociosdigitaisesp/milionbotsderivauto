import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface SecurityGateProps {
  children: React.ReactNode;
}

/**
 * Portão de Segurança - Componente que força a verificação de status
 * antes de permitir acesso a qualquer página protegida.
 * 
 * Lógica:
 * - Se o usuário está logado: Manda-o para VerificandoAcessoPage
 * - Se o usuário não está logado: Manda-o para LoginPage
 */
const SecurityGate: React.FC<SecurityGateProps> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Se o usuário está autenticado, redireciona para o Portão de Segurança
  // que fará a verificação do status antes de permitir acesso ao Dashboard
  return <Navigate to="/verificando-acesso" replace />;
};

export default SecurityGate;