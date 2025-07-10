
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '../../lib/supabaseClient';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, UserCheck, UserX, Clock, Shield } from 'lucide-react';

interface AdminStatsData {
  total_users: number;
  active_users: number;
  pending_users: number;
  inactive_users: number;
  expired_users: number;
  admin_users: number;
  new_users_30d: number;
}

const AdminStats = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      console.log('Buscando estatísticas de usuários...');
      
      const { data, error } = await supabase
        .from('profiles')
        .select('role, status, created_at');

      if (error) {
        console.error('Erro ao buscar estatísticas:', error);
        throw error;
      }

      console.log('Dados brutos das estatísticas:', data);

      // Calcular estatísticas manualmente
      const now = new Date();
      const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

      const stats: AdminStatsData = {
        total_users: data?.length || 0,
        active_users: data?.filter(u => u.status === 'active').length || 0,
        pending_users: data?.filter(u => u.status === 'pending').length || 0,
        inactive_users: data?.filter(u => u.status === 'inactive').length || 0,
        expired_users: data?.filter(u => u.status === 'expired').length || 0,
        admin_users: data?.filter(u => u.role === 'admin').length || 0,
        new_users_30d: data?.filter(u => new Date(u.created_at) >= thirtyDaysAgo).length || 0,
      };

      console.log('Estatísticas calculadas:', stats);
      return stats;
    },
    refetchInterval: 30000, // Atualizar a cada 30 segundos
  });

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Carregando...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-6 bg-muted animate-pulse rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const statCards = [
    {
      title: "Total de Usuários",
      value: stats?.total_users || 0,
      description: "Usuários registrados no sistema",
      icon: Users,
      color: "text-blue-600"
    },
    {
      title: "Usuários Pendentes",
      value: stats?.pending_users || 0,
      description: "Aguardando aprovação",
      icon: Clock,
      color: "text-yellow-600"
    },
    {
      title: "Usuários Ativos",
      value: stats?.active_users || 0,
      description: "Com acesso aprovado",
      icon: UserCheck,
      color: "text-green-600"
    },
    {
      title: "Administradores",
      value: stats?.admin_users || 0,
      description: "Usuários com privilégios admin",
      icon: Shield,
      color: "text-purple-600"
    },
    {
      title: "Usuários Inativos",
      value: stats?.inactive_users || 0,
      description: "Contas desativadas",
      icon: UserX,
      color: "text-red-600"
    },
    {
      title: "Novos (30 dias)",
      value: stats?.new_users_30d || 0,
      description: "Registrados nos últimos 30 dias",
      icon: Users,
      color: "text-indigo-600"
    }
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <Icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">{stat.description}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default AdminStats;
