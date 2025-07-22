import React from 'react';
import { BarChart3, TrendingUp, Activity } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
}

const LoadingState: React.FC<LoadingStateProps> = ({ 
  message = "Analisando dados dos bots..." 
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {/* Animação de loading principal */}
      <div className="relative mb-8">
        {/* Círculo externo rotativo */}
        <div className="w-20 h-20 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
        
        {/* Ícone central */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
            <BarChart3 className="text-primary animate-pulse" size={20} />
          </div>
        </div>
      </div>

      {/* Texto de loading */}
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-foreground mb-2">
          {message}
        </h3>
        <p className="text-sm text-muted-foreground max-w-md">
          Processando estatísticas de performance e organizando os resultados por assertividade.
        </p>
      </div>

      {/* Indicadores de progresso animados */}
      <div className="flex items-center gap-6 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
          <span>Coletando dados</span>
        </div>
        <div className="flex items-center gap-2">
          <TrendingUp size={14} className="text-emerald-500 animate-bounce" />
          <span>Calculando assertividade</span>
        </div>
        <div className="flex items-center gap-2">
          <Activity size={14} className="text-blue-500 animate-pulse" />
          <span>Organizando resultados</span>
        </div>
      </div>

      {/* Barra de progresso animada */}
      <div className="w-full max-w-md mt-8">
        <div className="h-1 bg-border/30 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-primary/50 to-primary rounded-full animate-pulse"></div>
        </div>
      </div>
    </div>
  );
};

export default LoadingState;