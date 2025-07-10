
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, UserCheck, UserX, Clock } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '../../lib/supabaseClient';

const AdminStats = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const { data: profiles, error } = await supabase
        .from('profiles')
        .select('status, expiration_date');

      if (error) throw error;

      const totalUsers = profiles.length;
      const activeUsers = profiles.filter(p => p.status === 'active').length;
      const inactiveUsers = profiles.filter(p => p.status === 'inactive').length;
      const expiredUsers = profiles.filter(p => p.status === 'expired').length;
      const usersWithExpiration = profiles.filter(p => p.expiration_date).length;

      return {
        totalUsers,
        activeUsers,
        inactiveUsers,
        expiredUsers,
        usersWithExpiration
      };
    }
  });

  const statCards = [
    {
      title: 'Total de Usuários',
      value: stats?.totalUsers || 0,
      icon: Users,
      description: 'Usuários registrados'
    },
    {
      title: 'Usuários Ativos',
      value: stats?.activeUsers || 0,
      icon: UserCheck,
      description: 'Com acesso ativo'
    },
    {
      title: 'Usuários Inativos',
      value: stats?.inactiveUsers || 0,
      icon: UserX,
      description: 'Acesso desabilitado'
    },
    {
      title: 'Com Expiração',
      value: stats?.usersWithExpiration || 0,
      icon: Clock,
      description: 'Possuem data de expiração'
    }
  ];

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              <div className="h-4 w-4 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-12 bg-muted animate-pulse rounded" />
              <div className="h-3 w-24 bg-muted animate-pulse rounded mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
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
