
import React from 'react';
import { useParams } from 'react-router-dom';
import { bots } from '../lib/mockData';
import BotDetailView from '../components/BotDetailView';

const BotDetail = () => {
  const { id } = useParams();
  const bot = bots.find(bot => bot.id === id);
  
  if (!bot) {
    return (
      <div className="container mx-auto py-12 text-center">
        <h1 className="text-2xl font-bold mb-4">Bot não encontrado</h1>
        <p className="text-muted-foreground">O bot que você está procurando não existe ou foi removido.</p>
        <a href="/" className="mt-4 inline-block text-primary hover:underline">Voltar para a biblioteca</a>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-6">
      <a href="/" className="text-primary hover:underline mb-8 block">&larr; Voltar para a biblioteca</a>
      <BotDetailView bot={bot} />
    </div>
  );
};

export default BotDetail;
