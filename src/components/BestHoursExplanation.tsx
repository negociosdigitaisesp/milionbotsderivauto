
import React, { useState } from 'react';
import { Clock } from 'lucide-react';

const BestHoursExplanation = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-gradient-to-r from-primary/5 to-primary/10 rounded-lg p-6 animate-fade-in">
      <div className="flex items-center gap-3 mb-3">
        <div className="bg-primary/20 p-3 rounded-full">
          <Clock className="text-primary" size={24} />
        </div>
        <h2 className="text-xl font-semibold">Melhores Horários dos Robôs</h2>
      </div>

      <div className={`overflow-hidden transition-all duration-500 ${isExpanded ? 'max-h-[1000px]' : 'max-h-28'}`}>
        <p className="text-muted-foreground mb-4">
          <strong className="text-foreground">Não existe um horário "melhor" para operar os robôs.</strong> O desempenho dos bots 
          no mercado de índices sintéticos, como o R_100, não é previsível por horário do dia, já que estes mercados são baseados 
          em algoritmos de números pseudoaleatórios que não seguem padrões temporais.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
          <div className="bg-background rounded-lg p-4 shadow-sm border border-border">
            <h3 className="font-medium mb-2 text-primary">1. Teste na Conta Demo</h3>
            <p className="text-sm">Sempre inicie testando o bot na conta demonstração para observar seu comportamento atual e 
            familiarizar-se com seu funcionamento antes de considerar usar em conta real.</p>
          </div>

          <div className="bg-background rounded-lg p-4 shadow-sm border border-border">
            <h3 className="font-medium mb-2 text-primary">2. Analise o Cenário</h3>
            <p className="text-sm">Observe se o bot está apresentando uma sequência positiva ou negativa. Mercados aleatórios como 
            o R_100 podem apresentar fases mais favoráveis a certos algoritmos.</p>
          </div>

          <div className="bg-background rounded-lg p-4 shadow-sm border border-border">
            <h3 className="font-medium mb-2 text-primary">3. Gestão de Risco</h3>
            <p className="text-sm">Mais importante que o horário é definir limites claros de perdas (Stop Loss) e ganhos (Stop Win) 
            antes de iniciar qualquer operação automatizada.</p>
          </div>
        </div>

        <div className="bg-primary/5 rounded-lg p-4 border border-primary/20">
          <h3 className="font-medium mb-2 text-primary flex items-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
            Dica Profissional
          </h3>
          <p className="text-sm">Em vez de focar em horários específicos, concentre-se em:</p>
          <ul className="text-sm mt-2 space-y-2">
            <li className="flex items-start">
              <span className="bg-primary/20 text-primary rounded-full w-5 h-5 flex items-center justify-center mr-2 mt-0.5">✓</span>
              <span>Testar o bot em diferentes momentos para entender seu comportamento em vários cenários</span>
            </li>
            <li className="flex items-start">
              <span className="bg-primary/20 text-primary rounded-full w-5 h-5 flex items-center justify-center mr-2 mt-0.5">✓</span>
              <span>Ajustar os parâmetros de gerenciamento de risco com base nos resultados observados</span>
            </li>
            <li className="flex items-start">
              <span className="bg-primary/20 text-primary rounded-full w-5 h-5 flex items-center justify-center mr-2 mt-0.5">✓</span>
              <span>Sempre usar valores que você pode se dar ao luxo de perder</span>
            </li>
          </ul>
        </div>
      </div>
      
      <button 
        onClick={() => setIsExpanded(!isExpanded)} 
        className="mt-4 text-primary hover:text-primary/80 text-sm font-medium flex items-center mx-auto"
      >
        {isExpanded ? 'Mostrar menos' : 'Saiba mais sobre horários'}
        <svg 
          width="20" 
          height="20" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          className={`ml-1 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        >
          <path d="M19 9l-7 7-7-7"/>
        </svg>
      </button>
    </div>
  );
};

export default BestHoursExplanation;
