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
        <h1 className="text-2xl font-bold mb-4">Bot no encontrado</h1>
        <p className="text-muted-foreground">El bot que estás buscando no existe o fue eliminado.</p>
        <a href="/" className="mt-4 inline-block text-primary hover:underline">Volver a la biblioteca</a>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-6">
      <a href="/" className="text-primary hover:underline mb-8 block">&larr; Volver a la biblioteca</a>
      
      <BotDetailView bot={bot} />
    </div>
  );
};

export default BotDetail;
