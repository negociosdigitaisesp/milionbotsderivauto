
import React, { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { supabase } from '../../lib/supabaseClient';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/components/ui/use-toast';
import { Calendar, Trash2 } from 'lucide-react';

interface UserProfile {
  id: string;
  full_name: string;
  email: string;
  role: 'admin' | 'user';
  status: 'active' | 'inactive' | 'expired';
  expiration_date: string | null;
  created_at: string;
}

interface UserExpirationModalProps {
  user: UserProfile | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

const UserExpirationModal: React.FC<UserExpirationModalProps> = ({
  user,
  open,
  onOpenChange,
  onSuccess
}) => {
  const [expirationDate, setExpirationDate] = useState('');
  const [expirationTime, setExpirationTime] = useState('23:59');

  useEffect(() => {
    if (user?.expiration_date) {
      const date = new Date(user.expiration_date);
      setExpirationDate(date.toISOString().split('T')[0]);
      setExpirationTime(date.toTimeString().slice(0, 5));
    } else {
      setExpirationDate('');
      setExpirationTime('23:59');
    }
  }, [user]);

  // Mutation para atualizar expiração
  const updateExpirationMutation = useMutation({
    mutationFn: async ({ userId, expirationDateTime }: { userId: string; expirationDateTime: string | null }) => {
      const { data, error } = await supabase
        .from('profiles')
        .update({ 
          expiration_date: expirationDateTime,
          ...(expirationDateTime && { status: 'active' })
        })
        .eq('id', userId)
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: (data) => {
      onSuccess();
      onOpenChange(false);
      toast({
        title: "Expiração atualizada",
        description: data.expiration_date 
          ? `Expiração definida para ${new Date(data.expiration_date).toLocaleString()}`
          : "Expiração removida",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Erro ao atualizar expiração",
        description: error.message,
        variant: "destructive",
      });
    }
  });

  const handleSave = () => {
    if (!user) return;

    let expirationDateTime: string | null = null;
    
    if (expirationDate) {
      // Validar se a data é futura
      const selectedDate = new Date(`${expirationDate}T${expirationTime}`);
      const now = new Date();
      
      if (selectedDate <= now) {
        toast({
          title: "Data inválida",
          description: "A data de expiração deve ser no futuro",
          variant: "destructive",
        });
        return;
      }
      
      expirationDateTime = selectedDate.toISOString();
    }

    updateExpirationMutation.mutate({
      userId: user.id,
      expirationDateTime
    });
  };

  const handleRemoveExpiration = () => {
    if (!user) return;
    
    updateExpirationMutation.mutate({
      userId: user.id,
      expirationDateTime: null
    });
  };

  const minDate = new Date().toISOString().split('T')[0];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Definir Data de Expiração
          </DialogTitle>
          <DialogDescription>
            Configure quando o acesso de <strong>{user?.full_name || user?.email}</strong> deve expirar.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="expiration-date">Data de Expiração</Label>
            <Input
              id="expiration-date"
              type="date"
              value={expirationDate}
              onChange={(e) => setExpirationDate(e.target.value)}
              min={minDate}
              className="w-full"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="expiration-time">Horário de Expiração</Label>
            <Input
              id="expiration-time"
              type="time"
              value={expirationTime}
              onChange={(e) => setExpirationTime(e.target.value)}
              className="w-full"
            />
          </div>

          {user?.expiration_date && (
            <div className="p-3 bg-muted rounded-md">
              <p className="text-sm text-muted-foreground">
                <strong>Expiração atual:</strong><br />
                {new Date(user.expiration_date).toLocaleString()}
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="flex gap-2">
          {user?.expiration_date && (
            <Button
              variant="outline"
              onClick={handleRemoveExpiration}
              disabled={updateExpirationMutation.isPending}
              className="flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Remover Expiração
            </Button>
          )}
          
          <Button
            onClick={handleSave}
            disabled={updateExpirationMutation.isPending}
            className="flex items-center gap-2"
          >
            {updateExpirationMutation.isPending ? 'Salvando...' : 'Salvar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default UserExpirationModal;
