
import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useAuth } from '../contexts/AuthContext';

interface UserStatus {
  status: 'active' | 'pending' | 'inactive' | 'expired';
  role: 'admin' | 'user';
  isApproved: boolean;
  loading: boolean;
}

export const useUserStatus = (): UserStatus => {
  const { user } = useAuth();
  const [status, setStatus] = useState<UserStatus>({
    status: 'pending',
    role: 'user',
    isApproved: false,
    loading: true
  });

  useEffect(() => {
    const checkUserStatus = async () => {
      if (!user) {
        setStatus(prev => ({ ...prev, loading: false }));
        return;
      }

      try {
        const { data: profile, error } = await supabase
          .from('profiles')
          .select('status, role')
          .eq('id', user.id)
          .single();

        if (error) {
          console.error('Erro ao verificar status do usuário:', error);
          setStatus(prev => ({ ...prev, loading: false }));
          return;
        }

        setStatus({
          status: profile?.status || 'pending',
          role: profile?.role || 'user',
          isApproved: profile?.status === 'active',
          loading: false
        });
      } catch (error) {
        console.error('Erro inesperado ao verificar status:', error);
        setStatus(prev => ({ ...prev, loading: false }));
      }
    };

    checkUserStatus();
  }, [user]);

  return status;
};
