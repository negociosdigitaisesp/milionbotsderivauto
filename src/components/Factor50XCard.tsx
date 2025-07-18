import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Star, Clock, Download, ChevronDown } from 'lucide-react';
import { cn } from '../lib/utils';
import { useToast } from '../hooks/use-toast';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface Factor50XCardProps {
  id: string;
  name: string;
  description: string;
  strategy: string;
  accuracy: number;
  operations: number;
  imageUrl: string;
  ranking?: number;
  isFavorite?: boolean;
  downloadUrls?: {
    conservative: string;
    intermediate: string;
    aggressive: string;
  };
}

const Factor50XCard = ({ 
  id, 
  name, 
  description, 
  strategy, 
  accuracy, 
  operations, 
  imageUrl,
  ranking,
  isFavorite: initialFavorite = false,
  downloadUrls = {
    conservative: '#',
    intermediate: '#',
    aggressive: '#'
  }
}: Factor50XCardProps) => {
  const [isFavorite, setIsFavorite] = useState(initialFavorite);
  const { toast } = useToast();

  const toggleFavorite = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsFavorite(!isFavorite);
    
    toast({
      title: !isFavorite ? "¡Bot añadido a favoritos!" : "¡Bot eliminado de favoritos!",
      description: !isFavorite ? `${name} ha sido añadido a tu lista de favoritos.` : `${name} ha sido eliminado de tu lista de favoritos.`,
      duration: 3000
    });
  };

  const handleDownload = (level: string, url: string) => {
    toast({
      title: "Descarga iniciada",
      description: `Descargando configuración ${level} de ${name}`,
      duration: 3000
    });
    // Aquí iría la lógica real de descarga
    window.open(url, '_blank');
  };

  // Get unique gradient and text styles based on bot ID
  const getBotStyles = (botId: string) => {
    return {
      gradient: "from-slate-900 via-slate-700 to-zinc-600",
      textGradient: "from-slate-100 to-white",
      accentColor: "bg-slate-400/10"
    };
  };

  const botStyle = getBotStyles(id);

  return (
    <div className="bot-card relative">
      {/* Ranking badge */}
      {ranking && (
        <div className="absolute top-0 left-0 z-10 bg-gradient-to-r from-emerald-600 to-emerald-500 text-white px-3 py-1 rounded-br-lg font-semibold shadow-md">
          #{ranking}
        </div>
      )}
      
      {/* Favorite button */}
      <button 
        onClick={toggleFavorite}
        className={cn(
          "absolute top-2 right-2 z-10 bg-black/50 rounded-full p-2 transition-all",
          "hover:bg-black/70 focus:outline-none"
        )}
        aria-label={isFavorite ? "Eliminar de favoritos" : "Añadir a favoritos"}
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
        {imageUrl ? (
          <img 
            src={imageUrl} 
            alt={name}
            className="w-full h-32 object-cover rounded-md"
          />
        ) : (
          <div className={`w-full h-32 bg-gradient-to-br ${botStyle.gradient} rounded-md flex items-center justify-center overflow-hidden relative`}>
            <div className="absolute inset-0 opacity-20">
              <div className="absolute top-0 left-0 w-full h-full bg-grid-white/10"></div>
              {/* Abstract pattern elements */}
              <div className={`absolute top-1/4 left-1/4 w-16 h-16 rounded-full ${botStyle.accentColor}`}></div>
              <div className={`absolute bottom-1/3 right-1/4 w-12 h-12 rounded-full ${botStyle.accentColor}`}></div>
              <div className={`absolute top-1/2 right-1/3 w-8 h-8 rounded-full ${botStyle.accentColor}`}></div>
            </div>
            <div className="z-10 text-center px-3">
              <h2 className={`text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r ${botStyle.textGradient} tracking-wider drop-shadow-sm`}>{name}</h2>
              <div className="mt-1 text-xs text-blue-100/90 font-medium uppercase tracking-wider">{strategy}</div>
            </div>
          </div>
        )}
        <div className="absolute bottom-2 right-2 bg-black/70 rounded-full px-2 py-1 text-xs flex items-center text-white">
          <Clock size={12} className="mr-1" /> {operations} ops
        </div>
      </div>
      
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-base line-clamp-1">{name}</h3>
        <span 
          className={cn(
            "text-xs px-3 py-1 rounded-full border shadow-sm flex items-center gap-1", 
            accuracy >= 60 ? "bg-gradient-to-r from-emerald-50 to-emerald-100 text-emerald-700 border-emerald-200" : 
            accuracy >= 40 ? "bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 border-blue-200" : 
            "bg-gradient-to-r from-rose-50 to-rose-100 text-rose-700 border-rose-200"
          )}
        >
          <span className={cn(
            "w-2 h-2 rounded-full",
            accuracy >= 60 ? "bg-emerald-500" : 
            accuracy >= 40 ? "bg-blue-500" : 
            "bg-rose-500"
          )}></span>
          {accuracy}% asertivo
        </span>
      </div>
      
      <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{description}</p>
      
      <div className="flex justify-between items-center">
        <span className="text-xs py-1 px-2 bg-primary/10 text-primary rounded-full">
          {strategy}
        </span>
        
        <Link 
          to={id === 'factor50x' ? '/factor50x' : `/bot/${id}`}
          className="text-xs text-primary hover:text-primary/80 flex items-center gap-1"
        >
          Detalles <ArrowRight size={12} />
        </Link>
      </div>

      {/* Factor50X Specific Download Section */}
      <div className="mt-4 pt-3 border-t border-border/50">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-medium py-2.5 px-4 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 shadow-sm hover:shadow-md">
              <Download size={16} />
              Obtener Configuraciones
              <ChevronDown size={14} />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent 
            align="center" 
            className="w-56 bg-card border border-border/50 shadow-lg rounded-lg p-1"
          >
            <DropdownMenuItem 
              onClick={() => handleDownload('Conservador', downloadUrls.conservative)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-md hover:bg-accent/50 cursor-pointer transition-colors"
            >
              <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm"></div>
              <div className="flex-1">
                <div className="font-medium text-sm">Nivel Conservador</div>
                <div className="text-xs text-muted-foreground">Riesgo bajo, ganancias estables</div>
              </div>
            </DropdownMenuItem>
            
            <DropdownMenuItem 
              onClick={() => handleDownload('Intermedio', downloadUrls.intermediate)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-md hover:bg-accent/50 cursor-pointer transition-colors"
            >
              <div className="w-3 h-3 rounded-full bg-yellow-500 shadow-sm"></div>
              <div className="flex-1">
                <div className="font-medium text-sm">Nivel Intermedio</div>
                <div className="text-xs text-muted-foreground">Equilibrio riesgo-beneficio</div>
              </div>
            </DropdownMenuItem>
            
            <DropdownMenuItem 
              onClick={() => handleDownload('Hard (Arriesgado)', downloadUrls.aggressive)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-md hover:bg-accent/50 cursor-pointer transition-colors"
            >
              <div className="w-3 h-3 rounded-full bg-red-500 shadow-sm"></div>
              <div className="flex-1">
                <div className="font-medium text-sm">Nivel Hard (Arriesgado)</div>
                <div className="text-xs text-muted-foreground">Alto riesgo, máximo potencial</div>
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};

export default Factor50XCard;