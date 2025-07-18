import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Factor50XTest = () => {
  return (
    <div className="container max-w-7xl mx-auto py-8 px-4">
      <div className="flex items-center gap-4 mb-8">
        <Link 
          to="/bots-apalancamiento" 
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft size={20} />
          <span>Volver a Bots de Apalancamiento</span>
        </Link>
      </div>
      
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">Factor50X - Página de Teste</h1>
        <p className="text-lg text-muted-foreground">
          Esta é uma versão simplificada para testar se a página está funcionando.
        </p>
      </div>
    </div>
  );
};

export default Factor50XTest;