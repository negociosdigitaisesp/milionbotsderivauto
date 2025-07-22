import React from 'react';
import { Skeleton } from '@/components/ui/skeleton';

const SkeletonCard = () => {
  return (
    <div className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-6 shadow-lg">
      {/* Borda superior */}
      <div className="absolute top-0 left-0 right-0 h-1">
        <Skeleton className="w-full h-full" />
      </div>
      
      {/* Badge de ranking */}
      <div className="absolute top-4 right-4">
        <Skeleton className="w-12 h-6 rounded-full" />
      </div>
      
      {/* Cabeçalho do card */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-3">
          <Skeleton className="w-12 h-12 rounded-xl" />
          <div className="flex-1">
            <Skeleton className="w-32 h-5 mb-1" />
          </div>
        </div>
        
        {/* Indicador de status */}
        <div className="flex items-center gap-2 mb-3">
          <Skeleton className="w-16 h-6 rounded-full" />
        </div>
      </div>
      
      {/* Porcentagem de assertividade */}
      <div className="text-center mb-6">
        <Skeleton className="w-20 h-14 mx-auto mb-2 rounded-lg" />
        <Skeleton className="w-24 h-4 mx-auto" />
      </div>
      
      {/* Barra de progresso */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <Skeleton className="w-16 h-3" />
          <Skeleton className="w-10 h-3" />
        </div>
        <Skeleton className="w-full h-3 rounded-full" />
      </div>
      
      {/* Estatísticas */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center p-3 bg-gradient-to-br from-emerald-500/5 to-emerald-500/10 rounded-lg border border-emerald-500/20">
          <Skeleton className="w-8 h-6 mx-auto mb-1" />
          <Skeleton className="w-12 h-3 mx-auto" />
        </div>
        <div className="text-center p-3 bg-gradient-to-br from-primary/5 to-primary/10 rounded-lg border border-primary/20">
          <Skeleton className="w-8 h-6 mx-auto mb-1" />
          <Skeleton className="w-8 h-3 mx-auto" />
        </div>
        <div className="text-center p-3 bg-gradient-to-br from-orange-500/5 to-orange-500/10 rounded-lg border border-orange-500/20">
          <Skeleton className="w-8 h-6 mx-auto mb-1" />
          <Skeleton className="w-12 h-3 mx-auto" />
        </div>
      </div>
      
      {/* Footer */}
      <div className="pt-4 border-t border-border/30">
        <div className="flex items-center justify-between mb-3">
          <Skeleton className="w-16 h-3" />
          <Skeleton className="w-12 h-3" />
        </div>
        
        {/* Métricas */}
        <div className="grid grid-cols-2 gap-3 text-xs mb-4">
          <div className="flex items-center justify-between">
            <Skeleton className="w-12 h-3" />
            <Skeleton className="w-8 h-3" />
          </div>
          <div className="flex items-center justify-between">
            <Skeleton className="w-16 h-3" />
            <Skeleton className="w-8 h-3" />
          </div>
        </div>
        
        {/* Botão */}
        <Skeleton className="w-full h-12 rounded-lg" />
      </div>
    </div>
  );
};

export default SkeletonCard;