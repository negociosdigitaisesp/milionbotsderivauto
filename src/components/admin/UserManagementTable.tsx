
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '../../lib/supabaseClient';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Search, MoreHorizontal, Calendar, Shield, User } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import UserExpirationModal from './UserExpirationModal';

interface UserProfile {
  id: string;
  full_name: string;
  email: string;
  role: 'admin' | 'user';
  status: 'active' | 'inactive' | 'expired' | 'pending';
  expiration_date: string | null;
  created_at: string;
  approved_at: string | null;
  approved_by: string | null;
}

const UserManagementTable = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedUser, setSelectedUser] = useState<UserProfile | null>(null);
  const [showExpirationModal, setShowExpirationModal] = useState(false);

  const queryClient = useQueryClient();

  // Buscar TODOS os usuários registrados
  const { data: users, isLoading, error } = useQuery({
    queryKey: ['admin-users', { search: searchTerm, role: roleFilter, status: statusFilter }],
    queryFn: async () => {
      console.log('Buscando usuários...');
      
      let query = supabase
        .from('profiles')
        .select('*')
        .order('created_at', { ascending: false });

      // Aplicar filtros apenas se especificados
      if (roleFilter !== 'all') {
        query = query.eq('role', roleFilter);
      }
      if (statusFilter !== 'all') {
        query = query.eq('status', statusFilter);
      }
      if (searchTerm) {
        query = query.or(`full_name.ilike.%${searchTerm}%,email.ilike.%${searchTerm}%`);
      }

      const { data, error } = await query;
      
      if (error) {
        console.error('Erro ao buscar usuários:', error);
        throw error;
      }
      
      console.log('Usuários encontrados:', data?.length || 0);
      console.log('Dados dos usuários:', data);
      
      return data as UserProfile[];
    },
    retry: 3,
    retryDelay: 1000,
  });

  // Mutation para aprovar usuário
  const approveUserMutation = useMutation({
    mutationFn: async ({ userId }: { userId: string }) => {
      const { data, error } = await supabase
        .from('profiles')
        .update({ 
          status: 'active',
          approved_at: new Date().toISOString()
        })
        .eq('id', userId)
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      toast.success(`Usuário ${data.email} aprovado com sucesso!`);
    },
    onError: (error: any) => {
      console.error('Erro ao aprovar usuário:', error);
      toast.error(`Erro ao aprovar usuário: ${error.message}`);
    }
  });

  // Mutation para atualizar status
  const updateStatusMutation = useMutation({
    mutationFn: async ({ userId, newStatus }: { userId: string; newStatus: string }) => {
      const { data, error } = await supabase
        .from('profiles')
        .update({ 
          status: newStatus,
          ...(newStatus === 'active' && { expiration_date: null })
        })
        .eq('id', userId)
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      toast.success(`Status do usuário atualizado para ${data.status}`);
    },
    onError: (error: any) => {
      console.error('Erro ao atualizar status:', error);
      toast.error(`Erro ao atualizar status: ${error.message}`);
    }
  });

  // Mutation para atualizar role
  const updateRoleMutation = useMutation({
    mutationFn: async ({ userId, newRole }: { userId: string; newRole: string }) => {
      const { data, error } = await supabase
        .from('profiles')
        .update({ role: newRole })
        .eq('id', userId)
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      toast.success(`Role do usuário atualizada para ${data.role}`);
    },
    onError: (error: any) => {
      console.error('Erro ao atualizar role:', error);
      toast.error(`Erro ao atualizar role: ${error.message}`);
    }
  });

  const getStatusBadge = (status: string) => {
    const variants = {
      active: 'default',
      inactive: 'secondary',
      expired: 'destructive',
      pending: 'outline'
    };
    const colors = {
      active: 'text-green-600',
      inactive: 'text-gray-500',
      expired: 'text-red-600',
      pending: 'text-yellow-600'
    };
    return (
      <Badge variant={variants[status as keyof typeof variants] as any} className={colors[status as keyof typeof colors]}>
        {status === 'pending' ? 'Pendente' : status}
      </Badge>
    );
  };

  const getRoleBadge = (role: string) => {
    return (
      <Badge variant={role === 'admin' ? 'default' : 'outline'}>
        {role === 'admin' ? <Shield className="h-3 w-3 mr-1" /> : <User className="h-3 w-3 mr-1" />}
        {role === 'admin' ? 'Administrador' : 'Usuário'}
      </Badge>
    );
  };

  const handleExpirationUpdate = (user: UserProfile) => {
    setSelectedUser(user);
    setShowExpirationModal(true);
  };

  if (isLoading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Carregando usuários...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-destructive mb-4">Erro ao carregar usuários: {error.message}</p>
        <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['admin-users'] })}>
          Tentar novamente
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="Buscar por nome ou email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={roleFilter} onValueChange={setRoleFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Filtrar por role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as roles</SelectItem>
            <SelectItem value="admin">Administrador</SelectItem>
            <SelectItem value="user">Usuário</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Filtrar por status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os status</SelectItem>
            <SelectItem value="pending">Pendente</SelectItem>
            <SelectItem value="active">Ativo</SelectItem>
            <SelectItem value="inactive">Inativo</SelectItem>
            <SelectItem value="expired">Expirado</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Informações de debug */}
      <div className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
        <p>Total de usuários encontrados: {users?.length || 0}</p>
        {users?.length === 0 && (
          <p className="text-yellow-600">
            Nenhum usuário encontrado. Verifique se a tabela 'profiles' existe no Supabase e possui dados.
          </p>
        )}
      </div>

      {/* Tabela */}
      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Data de Registro</TableHead>
              <TableHead>Expiração</TableHead>
              <TableHead className="w-[70px]">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users?.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="font-medium">{user.full_name || 'N/A'}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>{getRoleBadge(user.role)}</TableCell>
                <TableCell>{getStatusBadge(user.status)}</TableCell>
                <TableCell>
                  {user.created_at ? new Date(user.created_at).toLocaleDateString('pt-BR') : 'N/A'}
                </TableCell>
                <TableCell>
                  {user.expiration_date ? (
                    <span className="text-sm">
                      {new Date(user.expiration_date).toLocaleDateString('pt-BR')}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Ações do Usuário</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      
                      {/* Aprovar usuário pendente */}
                      {user.status === 'pending' && (
                        <DropdownMenuItem
                          onClick={() => approveUserMutation.mutate({ userId: user.id })}
                          className="text-green-600"
                        >
                          ✅ Aprovar Usuário
                        </DropdownMenuItem>
                      )}
                      
                      {/* Status Actions */}
                      <DropdownMenuItem
                        onClick={() => updateStatusMutation.mutate({ 
                          userId: user.id, 
                          newStatus: user.status === 'active' ? 'inactive' : 'active' 
                        })}
                      >
                        {user.status === 'active' ? '❌ Desativar' : '✅ Ativar'}
                      </DropdownMenuItem>
                      
                      {/* Role Actions - não permitir alterar o próprio admin */}
                      {user.email !== 'brendacostatrader@gmail.com' && (
                        <DropdownMenuItem
                          onClick={() => updateRoleMutation.mutate({ 
                            userId: user.id, 
                            newRole: user.role === 'admin' ? 'user' : 'admin' 
                          })}
                        >
                          {user.role === 'admin' ? '👤 Remover Admin' : '🛡️ Tornar Admin'}
                        </DropdownMenuItem>
                      )}
                      
                      <DropdownMenuSeparator />
                      
                      {/* Expiration */}
                      <DropdownMenuItem
                        onClick={() => handleExpirationUpdate(user)}
                      >
                        <Calendar className="h-4 w-4 mr-2" />
                        Definir Expiração
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {users?.length === 0 && !isLoading && (
        <div className="text-center py-8 text-muted-foreground">
          <p className="text-lg mb-2">Nenhum usuário encontrado</p>
          <p className="text-sm">
            Verifique se existem usuários registrados na tabela 'profiles' do Supabase
          </p>
        </div>
      )}

      {/* Modal de Expiração */}
      <UserExpirationModal
        user={selectedUser}
        open={showExpirationModal}
        onOpenChange={setShowExpirationModal}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['admin-users'] });
          queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
        }}
      />
    </div>
  );
};

export default UserManagementTable;
