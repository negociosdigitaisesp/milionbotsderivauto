import { verificarStatusDoUsuario, verificarStatusDoUsuarioSupabase } from '../services/verificarStatusDoUsuario';
import { supabase } from '../lib/supabaseClient';

/**
 * Exemplo de como usar a função verificarStatusDoUsuario
 * Este exemplo mostra como integrar a verificação de status com o fluxo de autenticação
 */
export async function exemploVerificacaoStatus() {
  try {
    // 1. Obter o usuário autenticado atual
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    
    if (authError || !user) {
      console.error('Usuário não autenticado:', authError);
      return;
    }
    
    // 2. Obter o token de acesso atual
    const { data: { session }, error: sessionError } = await supabase.auth.getSession();
    
    if (sessionError || !session?.access_token) {
      console.error('Erro ao obter sessão:', sessionError);
      return;
    }
    
    console.log('=== Exemplo de Verificação de Status do Usuário ===');
    console.log('User ID:', user.id);
    console.log('Auth Token:', session.access_token.substring(0, 50) + '...');
    
    // 3. Método 1: Usando a API REST diretamente
    console.log('\n--- Método 1: API REST Direta ---');
    const resultadoAPI = await verificarStatusDoUsuario(user.id, session.access_token);
    console.log('Resultado API:', resultadoAPI);
    
    // 4. Método 2: Usando o cliente Supabase (mais simples)
    console.log('\n--- Método 2: Cliente Supabase ---');
    const resultadoSupabase = await verificarStatusDoUsuarioSupabase(user.id);
    console.log('Resultado Supabase:', resultadoSupabase);
    
    // 5. Comparar resultados
    if (resultadoAPI.success && resultadoSupabase.success) {
      const apiStatus = resultadoAPI.isActive;
      const supabaseStatus = resultadoSupabase.isActive;
      
      console.log('\n--- Comparação de Resultados ---');
      console.log('Status via API:', apiStatus);
      console.log('Status via Supabase:', supabaseStatus);
      console.log('Resultados consistentes:', apiStatus === supabaseStatus);
    }
    
  } catch (error) {
    console.error('Erro no exemplo:', error);
  }
}

/**
 * Exemplo de integração com componente React
 * Mostra como usar a verificação de status em um hook personalizado
 */
export function useVerificacaoStatus() {
  const [status, setStatus] = React.useState<{
    loading: boolean;
    isActive: boolean | null;
    error: string | null;
  }>({ loading: true, isActive: null, error: null });
  
  React.useEffect(() => {
    async function verificarStatus() {
      try {
        setStatus({ loading: true, isActive: null, error: null });
        
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) {
          setStatus({ loading: false, isActive: null, error: 'Usuário não autenticado' });
          return;
        }
        
        const { data: { session } } = await supabase.auth.getSession();
        if (!session?.access_token) {
          setStatus({ loading: false, isActive: null, error: 'Sessão inválida' });
          return;
        }
        
        // Usar a função de verificação
        const resultado = await verificarStatusDoUsuario(user.id, session.access_token);
        
        if (resultado.success) {
          setStatus({ loading: false, isActive: resultado.isActive, error: null });
        } else {
          setStatus({ loading: false, isActive: false, error: resultado.error });
        }
        
      } catch (error) {
        setStatus({ 
          loading: false, 
          isActive: false, 
          error: error instanceof Error ? error.message : 'Erro desconhecido' 
        });
      }
    }
    
    verificarStatus();
  }, []);
  
  return status;
}

// Para testar no console do navegador:
// import { exemploVerificacaoStatus } from './src/examples/exemploVerificacaoStatus';
// exemploVerificacaoStatus();