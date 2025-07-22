import React, { useState } from 'react';
import { Clock, AlertCircle, Mail, ArrowLeft, RefreshCw } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from '../hooks/use-toast';

const PendingApprovalPage = () => {
  const { user, signOut, checkUserActiveStatus } = useAuth();
  const navigate = useNavigate();
  const [isChecking, setIsChecking] = useState(false);

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  // Função para verificar status manualmente
  const handleVerificarStatusManualmente = async () => {
    if (!user?.id) {
      toast.error('Usuário não encontrado');
      return;
    }

    setIsChecking(true);
    
    try {
      // Ação 1: Backend Query - Query Collection profiles
      const { isActive, error: statusError } = await checkUserActiveStatus(user.id);
      
      if (statusError) {
        console.error('Erro ao verificar status:', statusError);
        toast.error('Erro ao consultar o banco de dados: ' + statusError.message);
        return;
      }

      // Ação 2: Mostrar Alerta com o Resultado (Diagnóstico)
      const statusMessage = `Status de 'is_active' no banco de dados: ${isActive}`;
      toast.info(statusMessage);
      
      // Aguardar um momento para o usuário ver o diagnóstico
      setTimeout(() => {
        // Ação 3: Lógica Condicional
        if (isActive === true) {
          // IF TRUE: Navigate to Library (Ranking del Asertividad)
        toast.success('Conta ativada! Redirecionando para o ranking...');
        navigate('/', { replace: true });
        } else {
          // ELSE: Permanecer na PendingApprovalPage
          toast.warning('Sua conta ainda não foi ativada. Aguarde a aprovação do administrador.');
        }
      }, 2000); // 2 segundos para mostrar o diagnóstico
      
    } catch (error: any) {
      console.error('Erro inesperado:', error);
      toast.error('Erro inesperado ao verificar status: ' + error.message);
    } finally {
      setIsChecking(false);
    }
  };

  const handleGoBack = async () => {
    await signOut();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-card rounded-xl shadow-xl p-8 border border-border">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center mb-4">
            <Clock className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Cuenta Pendiente de Aprobación
          </h1>
          <p className="text-muted-foreground text-sm">
            Su cuenta ha sido creada exitosamente
          </p>
        </div>

        {/* Status Card */}
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-yellow-800 dark:text-yellow-200 text-sm mb-1">
                Esperando Activación
              </h3>
              <p className="text-yellow-700 dark:text-yellow-300 text-sm leading-relaxed">
                Su cuenta está siendo revisada por nuestro equipo. Recibirá una notificación por correo electrónico una vez que sea activada.
              </p>
            </div>
          </div>
        </div>

        {/* User Info */}
        {user?.email && (
          <div className="bg-muted/50 rounded-lg p-4 mb-6">
            <div className="flex items-center space-x-3">
              <Mail className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium text-foreground">
                  Correo registrado:
                </p>
                <p className="text-sm text-muted-foreground">
                  {user.email}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Information */}
        <div className="space-y-3 mb-8">
          <div className="text-sm text-muted-foreground">
            <h4 className="font-medium text-foreground mb-2">¿Qué sigue?</h4>
            <ul className="space-y-1 list-disc list-inside">
              <li>Nuestro equipo revisará su solicitud</li>
              <li>Le enviaremos un correo cuando sea aprobada</li>
              <li>Podrá acceder a todas las funcionalidades</li>
            </ul>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={handleVerificarStatusManualmente}
            disabled={isChecking}
            className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 px-4 rounded-lg transition-colors"
          >
            {isChecking ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Verificando...</span>
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                <span>Verificar Meu Status Manualmente</span>
              </>
            )}
          </button>
          
          <button
            onClick={handleGoBack}
            className="w-full flex items-center justify-center space-x-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground font-medium py-2.5 px-4 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Volver al Login</span>
          </button>
          
          <button
            onClick={handleSignOut}
            className="w-full text-muted-foreground hover:text-foreground font-medium py-2 px-4 rounded-lg transition-colors text-sm"
          >
            Cerrar Sesión
          </button>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-border text-center">
          <p className="text-xs text-muted-foreground">
            ¿Necesita ayuda? Contacte a nuestro equipo de soporte
          </p>
        </div>
      </div>
    </div>
  );
};

export default PendingApprovalPage;