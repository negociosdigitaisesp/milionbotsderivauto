
import React from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Heart } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/components/ui/use-toast";
import { useBots } from '@/hooks/useBots';
import { Bot } from '@/lib/mockData';

const MyBots = () => {
  const { data: bots, isLoading, error } = useBots();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const favoriteBots = bots?.filter(bot => bot.isFavorite) || [];

  const handleRemoveFromFavorites = (botId: string) => {
    // Get current bots
    const currentBots = queryClient.getQueryData(['bots']);
    
    // Update the favorite status
    queryClient.setQueryData(['bots'], (oldData: Bot[] | undefined) => {
      if (!oldData) return oldData;
      return oldData.map((bot) => {
        if (bot.id === botId) {
          return { ...bot, isFavorite: false };
        }
        return bot;
      });
    });

    // Show toast notification
    toast({
      title: "Removido dos favoritos",
      description: "Bot removido dos seus favoritos com sucesso.",
    });
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold">Meus Bots Favoritos</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="bg-muted h-32"></CardHeader>
              <CardContent className="mt-4">
                <div className="h-4 bg-muted rounded w-3/4 mb-4"></div>
                <div className="h-4 bg-muted rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-md">
          <p>Erro ao carregar seus bots favoritos. Por favor, tente novamente mais tarde.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold">Meus Bots Favoritos</h1>
      </div>

      {favoriteBots.length === 0 ? (
        <div className="text-center py-12 bg-muted/30 rounded-lg">
          <Heart className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h2 className="text-xl font-medium text-foreground mb-2">Nenhum bot favorito</h2>
          <p className="text-muted-foreground mb-6">Você ainda não adicionou nenhum bot aos seus favoritos.</p>
          <Button onClick={() => navigate('/')}>
            Explorar Bots
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {favoriteBots.map((bot) => (
            <Card key={bot.id} className="overflow-hidden hover:shadow-md transition-shadow">
              <CardHeader className="bg-gradient-to-r from-primary/10 to-primary/5 pb-8">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">{bot.name}</CardTitle>
                  <Button 
                    variant="ghost" 
                    size="icon"
                    className="h-8 w-8 text-primary"
                    onClick={() => handleRemoveFromFavorites(bot.id)}
                  >
                    <Heart className="h-5 w-5 fill-current" />
                    <span className="sr-only">Remover dos favoritos</span>
                  </Button>
                </div>
                <CardDescription>{bot.description.substring(0, 100)}...</CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Assertividade</span>
                  <span className="font-medium">{bot.accuracy}%</span>
                </div>
                <div className="w-full bg-muted h-2 rounded-full mt-1 mb-3">
                  <div 
                    className="h-2 rounded-full bg-primary" 
                    style={{ width: `${bot.accuracy}%` }}
                  ></div>
                </div>
              </CardContent>
              <CardFooter className="border-t pt-4 flex justify-between">
                <span className="text-xs text-muted-foreground">{bot.operations} operações</span>
                <Button variant="outline" size="sm" onClick={() => navigate(`/bot/${bot.id}`)}>
                  Ver Detalhes
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyBots;
