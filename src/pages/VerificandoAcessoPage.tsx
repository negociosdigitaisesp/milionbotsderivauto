import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { toast } from '../hooks/use-toast';
import { Loader2 } from 'lucide-react';
import { supabase } from '../lib/supabaseClient';

const VerificandoAcessoPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [dadosDoPerfil, setDadosDoPerfil] = useState<any>(null);

  useEffect(() => {
    // On Page Load: Implementação do Portão de Segurança
    const portaoDeSeguranca = async () => {
      try {
        // Verificar se o usuário está autenticado
        if (!user?.id) {
          console.error('Usuário não encontrado após login');
          navigate('/login', { replace: true });
          return;
        }

        // Ação 1: Backend Query para buscar o perfil na tabela profiles
        // Filtro: id igual ao Authenticated User ID
        // Nome da saída: dadosDoPerfil
        const { data: dadosDoPerfil, error } = await supabase
          .from('profiles')
          .select('is_active')
          .eq('id', user.id)
          .single();

        if (error) {
          console.error('Erro ao buscar perfil:', error);
          navigate('/pending-approval', { replace: true });
          return;
        }

        // Armazenar resultado da consulta
        setDadosDoPerfil(dadosDoPerfil);

        // Ação 2: Delay de 500 milissegundos
        // Permite que o estado de autenticação se propague corretamente
        await new Promise(resolve => setTimeout(resolve, 500));

        // Ação 3: Conditional Actions baseada no resultado da consulta
         // Condição IF: Action Output -> dadosDoPerfil -> is_active Is Equal To True
         if (dadosDoPerfil && dadosDoPerfil.is_active === true) {
           // No Bloco IF TRUE: Navigate To Library (Ranking del Asertividad) (com Replace Route)
        navigate('/', { replace: true });
         } else {
           // No Bloco ELSE: Navigate To PendingApprovalPage (com Replace Route)
           navigate('/pending-approval', { replace: true });
         }
        
      } catch (error: any) {
        console.error('Erro no Portão de Segurança:', error);
        // Em caso de erro, redirecionar para pending approval por segurança
        navigate('/pending-approval', { replace: true });
      }
    };

    // Executar o Portão de Segurança ao carregar a página
    portaoDeSeguranca();
  }, [user, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4">
        {/* Indicador de progresso circular */}
        <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
        <h2 className="text-xl font-semibold text-foreground">
          Verificando acesso...
        </h2>
        <p className="text-muted-foreground">
          Aguarde enquanto validamos suas permissões
        </p>
      </div>
    </div>
  );
};

export default VerificandoAcessoPage;