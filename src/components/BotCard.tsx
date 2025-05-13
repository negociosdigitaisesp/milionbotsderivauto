
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Star, Clock } from 'lucide-react';
import { cn } from '../lib/utils';
import { useToast } from '../hooks/use-toast';
import { Bot } from '@/lib/mockData';

interface BotCardProps {
  bot: Bot;
  onFavoriteToggle: (botId: string) => void;
}

const BotCard = ({ bot, onFavoriteToggle }: BotCardProps) => {
  const [isFavorite, setIsFavorite] = useState(bot.isFavorite);
  const { toast } = useToast();

  const toggleFavorite = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsFavorite(!isFavorite);
    onFavoriteToggle(bot.id);
    
    toast({
      title: !isFavorite ? "Bot adicionado aos favoritos!" : "Bot removido dos favoritos!",
      description: !isFavorite ? `${bot.name} foi adicionado à sua lista de favoritos.` : `${bot.name} foi removido da sua lista de favoritos.`,
      duration: 3000
    });
  };

  return (
    <div className="bot-card relative">
      {/* Ranking badge */}
      {bot.ranking && (
        <div className="absolute top-0 left-0 z-10 bg-gradient-to-r from-primary/90 to-primary/70 text-white px-3 py-1 rounded-br-lg font-semibold shadow-md">
          #{bot.ranking}
        </div>
      )}
      
      {/* Favorite button */}
      <button 
        onClick={toggleFavorite}
        className={cn(
          "absolute top-2 right-2 z-10 bg-black/50 rounded-full p-2 transition-all",
          "hover:bg-black/70 focus:outline-none"
        )}
        aria-label={isFavorite ? "Remover dos favoritos" : "Adicionar aos favoritos"}
      >
        <Star 
          size={16} 
          className={cn(
            "transition-colors", 
            isFavorite ? "fill-yellow-400 text-yellow-400" : "text-white"
          )} 
        />
      </button>

      <div className="relative mb-3">
        <img 
          src={bot.imageUrl} 
          alt={bot.name}
          className="w-full h-32 object-cover rounded-md"
        />
        <div className="absolute bottom-2 right-2 bg-black/70 rounded-full px-2 py-1 text-xs flex items-center text-white">
          <Clock size={12} className="mr-1" /> {bot.operations} ops
        </div>
      </div>
      
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-base line-clamp-1">{bot.name}</h3>
        <span 
          className={cn(
            "text-xs px-2 py-1 rounded-full", 
            bot.accuracy >= 60 ? "bg-success/10 text-success" : 
            bot.accuracy >= 40 ? "bg-warning/10 text-warning" : 
            "bg-danger/10 text-danger"
          )}
        >
          {bot.accuracy}% assertivo
        </span>
      </div>
      
      <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{bot.description}</p>
      
      <div className="flex justify-between items-center">
        <span className="text-xs py-1 px-2 bg-primary/10 text-primary rounded-full">
          {bot.strategy}
        </span>
        
        <Link 
          to={`/bot/${bot.id}`}
          className="text-xs text-primary hover:text-primary/80 flex items-center gap-1"
        >
          Detalhes <ArrowRight size={12} />
        </Link>
      </div>
    </div>
  );
};

export default BotCard;
