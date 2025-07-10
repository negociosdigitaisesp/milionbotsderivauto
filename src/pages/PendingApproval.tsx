
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '../contexts/AuthContext';
import { Clock, Mail, Shield } from 'lucide-react';

const PendingApproval = () => {
  const { signOut, user } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100">
            <Clock className="h-6 w-6 text-amber-600" />
          </div>
          <CardTitle className="text-xl">Aguardando Aprovação</CardTitle>
          <CardDescription className="text-center">
            Sua conta foi criada com sucesso, mas precisa ser aprovada por um administrador antes que você possa acessar o sistema.
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <div className="rounded-lg bg-muted p-4">
            <div className="flex items-center gap-2 text-sm">
              <Mail className="h-4 w-4" />
              <span className="font-medium">Email registrado:</span>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{user?.email}</p>
          </div>
          
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Shield className="h-4 w-4" />
              Próximos passos:
            </div>
            <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
              <li>• Aguarde a aprovação do administrador</li>
              <li>• Você receberá uma notificação quando aprovado</li>
              <li>• Em caso de dúvidas, entre em contato conosco</li>
            </ul>
          </div>
          
          <div className="pt-4">
            <Button 
              variant="outline" 
              className="w-full"
              onClick={signOut}
            >
              Sair da Conta
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PendingApproval;
