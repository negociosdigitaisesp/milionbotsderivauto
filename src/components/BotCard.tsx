
import React from 'react';
import { Link } from 'react-router-dom';
import { Download, ArrowRight } from 'lucide-react';
import { cn } from '../lib/utils';

interface BotCardProps {
  id: string;
  name: string;
  description: string;
  strategy: string;
  accuracy: number;
  downloads: number;
  imageUrl: string;
}

const BotCard = ({ 
  id, 
  name, 
  description, 
  strategy, 
  accuracy, 
  downloads, 
  imageUrl 
}: BotCardProps) => {
  return (
    <div className="bot-card">
      <div className="relative mb-3">
        <img 
          src={imageUrl} 
          alt={name}
          className="w-full h-32 object-cover rounded-md"
        />
        <div className="absolute top-2 right-2 bg-black/70 rounded-full px-2 py-1 text-xs">
          {downloads} <Download size={12} className="inline ml-1" />
        </div>
      </div>
      
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-base line-clamp-1">{name}</h3>
        <span 
          className={cn(
            "text-xs px-2 py-1 rounded-full", 
            accuracy >= 60 ? "bg-success/10 text-success" : 
            accuracy >= 40 ? "bg-warning/10 text-warning" : 
            "bg-danger/10 text-danger"
          )}
        >
          {accuracy}% assertivo
        </span>
      </div>
      
      <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{description}</p>
      
      <div className="flex justify-between items-center">
        <span className="text-xs py-1 px-2 bg-primary/10 text-primary rounded-full">
          {strategy}
        </span>
        
        <Link 
          to={`/bot/${id}`}
          className="text-xs text-primary hover:text-primary/80 flex items-center gap-1"
        >
          Detalhes <ArrowRight size={12} />
        </Link>
      </div>
    </div>
  );
};

export default BotCard;
