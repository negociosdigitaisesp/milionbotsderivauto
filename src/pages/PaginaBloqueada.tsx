import React from "react";

const PaginaBloqueada: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <h1 className="text-3xl md:text-5xl font-bold text-center text-red-600">
        ACESSO NEGADO. AGUARDANDO APROVAÇÃO.
      </h1>
    </div>
  );
};

export default PaginaBloqueada;